from datetime import date, timedelta, datetime
import os
from pydriller import Repository, Git
from DataCollectors.ScraperGit import Collector
from helpers import get_first_and_last_commit, get_commit_count, get_list_of_files
import lizard
import pandas as pd
import matplotlib.pyplot as plt

file_prefix = os.getcwd() + '/go-ipfs/'

#repo = 'https://github.com/ipfs/go-ipfs.git'
repo_path = 'go-ipfs'
branch = 'release-v0.10.0'
start_date = datetime(2019, 1, 1)
end_date = datetime.now() # the branch release-v0.10.0 was released on the 30th September 2021

if __name__ == '__main__':

    print(f'\nInvestigating repository "{repo_path}" ({branch}) from {start_date} to {end_date}')
    repo = Repository(repo_path, since=start_date, to=end_date, only_in_branch=branch)

    first_commit, last_commit = get_first_and_last_commit(repo)
    commit_count = get_commit_count(repo)
    print(f'- There are a total of {commit_count} commits.\n   - first commit: {first_commit.hash}\n   - last commit: {last_commit.hash}')

    # list with all existing files in the repo
    files = get_list_of_files(repo_path, last_commit.hash, ['go'])
    print(f'- Files of attention: {len(files)}')

    file_data = {}
    for file_name in files:
        file_information = lizard.analyze_file(file_name)
        functions = []
        for function in file_information.function_list:
            functions.append(function.__dict__)
        file_name_without_prefix = file_name.replace(file_prefix, '')
        file_data[file_name_without_prefix] = {
            'modified': 0,
            'nloc': file_information.nloc,
            'token_count': file_information.token_count,
            'function_count': len(functions),
            'functions': functions
        }

    for commit in repo.traverse_commits():
        for m in commit.modified_files:
            file_name = m.new_path
            if file_name not in file_data:
                # modified file does not exist at current commit
                continue
            file_data[file_name]['modified'] += 1

    # convert to dataframe and save as .csv
    df = pd.DataFrame.from_dict(file_data, orient='index')
    df.to_csv('results/file_list.csv', encoding='utf-8', index=True)

    # naive plotting of complexity hotspots
    fig, ax = plt.subplots(figsize=(10,10))
    ax.scatter(df['nloc'], df['modified'])
    ax.set_xlabel('nloc')
    ax.set_ylabel('modifications')
    ax.set_title('Complexity hotspots')
    plt.savefig('results/complexity_hotspots', bbox_inches='tight')
