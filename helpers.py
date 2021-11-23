from datetime import date, timedelta, datetime
import os
from pydriller import Repository, Git
import lizard
import pandas as pd

def get_first_and_last_commit(repo):
    first_commit = next(repo.traverse_commits(), None)
    last_commit = None
    for commit in repo.traverse_commits():
        last_commit = commit
    return first_commit, last_commit

def get_commit_count(repo):
    commit_count = 0
    for commit in repo.traverse_commits():
        commit_count += 1
    return commit_count

def get_list_of_files(repo_path, last_commit_hash, file_types=None):
    gr = Git(repo_path)
    gr.checkout(last_commit_hash)
    files = gr.files()
    if file_types:
        filtered = []
        for file_name in files:
            type = file_name.split('.')[-1]
            if type in file_types:
                filtered.append(file_name)
        return filtered
    else:
        return files