#!/usr/bin/env python3

import os
import sys
import subprocess
from config import key
from config import owners
from github import Github, GithubException

def print_help():
    '''
    Print help describing the syntax for how to use the program.

    Parameters:
        - None

    Returns:
        - None
    '''
    print("Usage {} <action> [--organization/-o=<organization>] <search string>".format(sys.argv[0]))
    print("Available actions:")
    print("    ls")
    print("    push")
    print("    push-interactive")
    print("    clone")
    print("    set_readonly")


def is_matching(repo, project, organization):
    '''
    Check if a repo matches with a project and potential organization
    If an organization is provided, make sure the repo is owned by it,
    and that the project name is in the repo name. If an organization is
    not provided, simply make sure the project matches.

    Parameters:
        - Repo which is the repository queried from github
        - Project name to be queried (repo name should contain this)
        - Organization name which should own the repo

    Returns:
        - True if repo matches project and organization provided
        - False if otherwise
    '''
    if organization:
        if project in repo.name and organization == repo.owner.login:
            return True
    else:
        if project in repo.name:
            return True

    return False


def add_commit_push(project, interactive):
    '''
    Adds a file, commits it and pushed to the git repos
    which are present in a project directory.

    Will be used to specify if a student has passed, or failed.

    Parameters:
        - Project which should match the name of the sub-directory containing
          the git repositories which should be added, committed and pushed to.
        - Interactive parameter determining if the commit should be interactive or not

    Returns:
        - None
    '''
    if interactive:
        passed = "Result: PASS"
        failed = "Result: FAIL"

    project_dir = "{}/{}".format(os.getcwd(), project)
    repos = os.listdir(project_dir)
    for repo in repos:
        repo_dir = "{}/{}".format(project_dir, repo)
        if os.path.isdir(repo_dir):
            if interactive:
                inp = input(f"Did {repo} pass or fail? Type 'fail' for fail. [Default: pass]: ")
                if inp == "fail":
                    result = failed
                elif inp == "skip":
                    continue
                else:
                    result = passed
                text = ""
            else:
                result = "GRADING"
                print(f"\nGrading {repo} - enter grading comment:")
                text = sys.stdin.read()

            with open(f"{repo_dir}/{result}", "w+") as f:
                f.write(text)

            subprocess.run(["git", "add", result], cwd = repo_dir)
            subprocess.run(["git", "commit", "-m", f"Graded project, see the {result}-file in the root directory"], cwd = repo_dir)
            subprocess.run(["git", "push"], cwd = repo_dir)
            print("Pushed changes to github")
        else:
            print(f"\n{repo} is not a directory, and can't be a repo")

def list_matching(project, organization):
    '''
    Lists the repositories matching the provided project and organization.

    Parameters:
        - Project name to be queried (repo name should contain this)
        - Organization name which should own the repo (if any)

    Returns:
        - None
    '''
    g = Github(key)
    for repo in g.get_user().get_repos():
        if is_matching(repo, project, organization):
            print(repo.name)

def set_matching_readonly(project, organization):
    '''
    Sets the matching repositories to read-only for all non-owners.
    Can be used to revoke students' write permissions.

    PS: Will ONLY work if the github library is modified.
        See github.com/NikolaiMagnussen/pygithub.

    Parameters:
        - Project name to be queried (repo name should contain this)
        - Organization name which should own the repo (if any)

    Returns:
        - None
    '''
    g = Github(key)
    for repo in g.get_user().get_repos():
        if is_matching(repo, project, organization):
            print("Changing permissions for {}".format(repo.name))
            for collab in repo.get_collaborators():
                if not collab.login in owners:
                    # Student found. change permissions from push to pull
                    repo.remove_from_collaborators(collab)
                    try:
                        repo.add_to_collaborators(collab, "pull")
                        print("    {} can only read".format(collab.login))
                    except GithubException as e:
                        print(e)
                        repo.add_to_collaborators(collab)
                        print("    {} can still write because readonly is only possible for organizations".format(collab.login))
                else:
                    print("    Owner: {}".format(collab.login))

def clone_matching(project, organization):
    '''
    Clone the matching repositories to a project directory.

    Parameters:
        - Project name to be queried (repo name should contain this)
        - Organization name which should own the repo (if any)

    Returns:
        - None
    '''
    project_dir = "{}/{}".format(os.getcwd(), project)
    g = Github(key)
    for repo in g.get_user().get_repos():
        if is_matching(repo, project, organization):
            if not os.path.isdir(project_dir):
                os.mkdir(project_dir)
            split_idx = repo.clone_url.find("github.com")
            repo_url = "{}{}@{}".format(repo.clone_url[:split_idx], key, repo.clone_url[split_idx:])
            subprocess.run(["git", "clone", repo_url], cwd = project_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_help()
        sys.exit(1)

    action = sys.argv[1]
    if "--organization=" in sys.argv[2] or "-o=" in sys.argv[2]:
        organization = sys.argv[2].split("=")[1]
        project = sys.argv[3]
    else:
        if len(sys.argv) > 3:
            print_help()
            sys.exit(1)
        project = sys.argv[2]
        organization = None

    if action == "ls":
        list_matching(project, organization)
    elif action == "clone":
        clone_matching(project, organization)
    elif action == "set_readonly":
        print("Are you sure you want to set all non-owners of the matching repos to read-only?")
        print("Type 'YES' to confirm")
        ans = input()
        if ans == "YES":
            set_matching_readonly(project, organization)
    elif action == "push-interactive":
        if organization is not None:
            print("Organization does not affect pushing")
        add_commit_push(project, interactive=True)
    elif action == "push":
        if organization is not None:
            print("Organization does not affect pushing")
        add_commit_push(project, interactive=False)
    else:
        print_help()
