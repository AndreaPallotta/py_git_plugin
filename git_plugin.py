#!/usr/bin/env python3
import os
import click
import subprocess
from subprocess import CalledProcessError

def __run(command, cwd):
    try:
        result = subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"'{' '.join(command)}' executed successfully\n{result.stdout}")
        return result
    except CalledProcessError as e:
        print(f"Error running '{' '.join(command)}': {e.stderr}")
        return e

def _find_git_folder(path):
    if not os.path.isdir(path):
        return None
    for el in os.listdir(path):
        el_path = os.path.join(path, el)
        if os.path.isdir(el_path) and el == ".git":
            return el_path
    return None

def get_commit_list(directory):
    try:
        result = __run(["git", "log", "--oneline"], directory)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
    except CalledProcessError as e:
        print(f"Error retrieving commit list: {e.stderr}")
    return []

def cherry_pick_commits(commits, target_branch, directory, auto_resolve=False):
    try:
        __run(["git", "checkout", target_branch], directory)
        for commit in commits:
            result = __run(["git", "cherry-pick", commit], directory)
            if result.returncode != 0:
                if auto_resolve:
                    __run(["git", "cherry-pick", "--skip"], directory)
                    print(f"Automatically skipped commit {commit} due to conflicts.")
                else:
                    print(f"Conflict detected while cherry-picking commit {commit}. Aborting...")
                    __run(["git", "cherry-pick", "--abort"], directory)
                    break
        print(f"Cherry-picked commits {commits} onto {target_branch} successfully.")
    except CalledProcessError as e:
        print(f"Error during cherry-pick process: {e.stderr}")
        __run(["git", "cherry-pick", "--abort"], directory)
        print("Cherry-pick aborted due to conflict.")

@click.group()
@click.option("-p", "--path", default=".", type=str, help="Target path to search")
@click.pass_context
def cli(ctx, path):
    absolute_path = os.path.abspath(path)
    git_path = _find_git_folder(absolute_path)
    if not git_path:
        print(f"{absolute_path} is not a git project directory")
        ctx.exit()
    parent_dir = os.path.dirname(git_path)
    ctx.obj = {
        'path': absolute_path,
        'git_path': git_path,
        'parent_dir': parent_dir
    }

@cli.command()
@click.pass_context
def pull(ctx):
    parent_dir = ctx.obj['parent_dir']
    __run(["git", "pull"], parent_dir)

@cli.command()
@click.option("-m", "--message", default="Default commit", type=str, help="Commit message for --push")
@click.pass_context
def push(ctx, message):
    parent_dir = ctx.obj['parent_dir']
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
    parent_dir = ctx.obj['parent_dir']
    if interactive:
        commits = get_commit_list(parent_dir)
        for i, commit in enumerate(commits):
            print(f"{i}: {commit}")
        selected_commits = click.prompt("Enter the numbers of commits to cherry-pick, separated by commas", type=str)
        selected_indices = [int(x) for x in selected_commits.split(",")]
        cherry_pick = [commits[i].split()[0] for i in selected_indices]
    if cherry_pick and branch:
        cherry_pick_commits(cherry_pick, branch, parent_dir, auto_resolve)

if __name__ == "__main__":
    cli()