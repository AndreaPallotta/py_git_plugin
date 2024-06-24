#!/usr/bin/env python3
import os
import click
import subprocess
import configparser
import re
from texttable import Texttable

CONFIG_FILE = os.path.expanduser("~/.gitconfig")
config = configparser.ConfigParser()

if os.path.exists(CONFIG_FILE):
    config.read(CONFIG_FILE)

def __run(command, cwd):
    try:
        result = subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        click.echo(f"'{' '.join(command)}' executed successfully\n{result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running '{' '.join(command)}': {e.stderr}")
        return e

def _find_git_folder(path):
    if not os.path.isdir(path):
        return None
    for el in os.listdir(path):
        el_path = os.path.join(path, el)
        if os.path.isdir(el_path) and el == ".git":
            return el_path
    return None

def _get_commit_list(directory):
    try:
        result = __run(["git", "log", "--oneline"], directory)
        if result.returncode == 0:
            return result.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error retrieving commit list: {e.stderr}")
    return []

def _cherry_pick_commits(commits, target_branch, directory, auto_resolve=False):
    try:
        __run(["git", "checkout", target_branch], directory)
        for commit in commits:
            result = __run(["git", "cherry-pick", commit], directory)
            if result.returncode != 0:
                if auto_resolve:
                    __run(["git", "cherry-pick", "--skip"], directory)
                    click.echo(f"Automatically skipped commit {commit} due to conflicts.")
                else:
                    click.echo(f"Conflict detected while cherry-picking commit {commit}. Aborting...")
                    __run(["git", "cherry-pick", "--abort"], directory)
                    break
        click.echo(f"Cherry-picked commits {commits} onto {target_branch} successfully.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error during cherry-pick process: {e.stderr}")
        __run(["git", "cherry-pick", "--abort"], directory)
        click.echo("Cherry-pick aborted due to conflict.")

def _sanitize_alias(name):
    """Sanitize alias name to remove invalid characters."""
    reg = re.compile('[^a-zA-Z]')
    return reg.sub('', name)

@click.group()
@click.option("-p", "--path", default=".", type=str, help="Target path to search")
@click.pass_context
def cli(ctx, path):
    absolute_path = os.path.abspath(path)
    git_path = _find_git_folder(absolute_path)
    if not git_path:
        click.echo(f"{absolute_path} is not a git project directory")
        ctx.exit()
    parent_dir = os.path.dirname(git_path)
    ctx.obj = {
        "path": absolute_path,
        "git_path": git_path,
        "parent_dir": parent_dir
    }

@cli.command()
@click.option("-m", "--message", default="Default commit", type=str, help="Commit message for --push")
@click.pass_context
def push(ctx, message):
    """Add, commit with message, and push"""
    parent_dir = ctx.obj["parent_dir"]
    __run(["git", "add", "."], parent_dir)
    __run(["git", "commit", "-m", message], parent_dir)
    __run(["git", "push"], parent_dir)

@cli.command()
@click.option("--cherry-pick", multiple=True, type=str, help="Cherry-pick specified commit(s)")
@click.option("--branch", default="", type=str, help="Target branch for cherry-picking")
@click.option("--auto-resolve", is_flag=True, help="Automatically resolve conflicts by skipping problematic commits")
@click.option("--interactive", is_flag=True, help="Interactively select commits to cherry-pick")
@click.pass_context
def cherry_pick(ctx, cherry_pick, branch, auto_resolve, interactive):
    """Interactive cherry-picking"""
    parent_dir = ctx.obj["parent_dir"]
    if interactive:
        commits = _get_commit_list(parent_dir)
        for i, commit in enumerate(commits):
            print(f"{i}: {commit}")
        selected_commits = click.prompt("Enter the numbers of commits to cherry-pick, separated by commas", type=str)
        selected_indices = [int(x) for x in selected_commits.split(",")]
        cherry_pick = [commits[i].split()[0] for i in selected_indices]
    if cherry_pick and branch:
        _cherry_pick_commits(cherry_pick, branch, parent_dir, auto_resolve)

@cli.command()
@click.argument("name")
@click.argument("command")
def alias_add(name, command):
    """Add new alias."""
    name = _sanitize_alias(name)
    if "alias" not in config:
        config["alias"] = {}
    if name in config["alias"]:
        click.echo(f"Alias '{name}' already exists")
        return
    config["alias"][_sanitize_alias(name)] = command
    with open(CONFIG_FILE, "w") as config_file:
        config.write(config_file)
    click.echo(f"Alias '{name}' added for command '{command}'")

@cli.command()
@click.argument("name")
def alias_remove(name):
    """Remove alias."""
    if "alias" not in config:
        click.echo(f"Cannot delete '{name}'. No aliases found")
        return

    if name in config["alias"]:
        del config["alias"][name]
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        click.echo(f"Alias '{name}' removed.")
    else:
        click.echo(f"Alias '{name}' does not exist.")

@cli.command()
def alias_list():
    """List all defined aliases."""
    if "alias" in config:
        t = Texttable()
        t.add_row(["Alias", "Command"])
        if config["alias"].__len__() == 0:
            t.add_row(["No aliases found", ""])
        else:
            for alias, command in config["alias"].items():
                t.add_row([alias, command])
        click.echo(t.draw())
    else:
        click.echo("No aliases defined.")

@cli.command()
def alias_clear():
    """Clear all defined aliases."""
    config["alias"] = {}
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)
    click.echo("All aliases cleared.")

@cli.command()
@click.argument("alias_name")
@click.argument("args", nargs=-1)
def run_alias(alias_name, args):
    """Run a command using an alias."""
    if alias_name in config["alias"]:
        command = config["alias"][alias_name]
        full_command = command.split() + list(args)
        subprocess.run(full_command)
    else:
        click.echo(f"Alias '{alias_name}' not found.")

if __name__ == "__main__":
    cli()