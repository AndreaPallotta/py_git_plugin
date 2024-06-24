#!/usr/bin/env python3
import os
import click
import subprocess

def __run(command, cwd):
    try:
        result = subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"'{" ".join(command)}' executed successfully\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error running '{" ".join(command)}': {e.stderr}")

def _walk_dir(path):    
    if not os.path.isdir(path):
        print(f"{path} is not a directory")
        return False
    for el in os.listdir(path):
        el_path = os.path.join(path, el)
        if os.path.isdir(el_path) and os.path.basename(el_path) == ".git":
            return True
    return False

@click.command()
@click.option("-p", "--path", default=".", type=str, help="Target path to search")
@click.option("--pull", is_flag=True, help="Pull latest changes")
@click.option("--push", is_flag=True, help="Add edited files, commits with message, and pushes")
@click.option("-m", "--message", default="Default commit", type=str, help="Commit message for --push")
def run(path, pull, push, message):
    absolute_path = os.path.abspath(path)
    is_git_project = _walk_dir(absolute_path)
    if not is_git_project:
        print(f"{absolute_path} is not a git project directory")
        return
    
    print(f"git folder found in: {path}")
    if pull:
        __run(["git", "pull"], path)
    elif push:
        __run(["git", "add", "."], path)
        __run(["git", "commit", "-m", message], path)
        __run(["git", "push",], path)

if __name__ == "__main__":
    run()