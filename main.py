from datetime import date, timedelta, datetime
import os
from pydriller import Repository, Git
from DataCollectors.ScraperGit import Collector
from helpers import get_first_and_last_commit, get_commit_count, get_list_of_files
import lizard
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
#plt.style.use('fivethirtyeight')

file_prefix = os.getcwd() + '/go-ipfs/'

#repo = 'https://github.com/ipfs/go-ipfs.git'
repo_path = 'go-ipfs'
branch = 'release-v0.10.0'
start_date = datetime(2021, 1, 1)
end_date = datetime.now() # the branch release-v0.10.0 was released on the 30th September 2021

if __name__ == '__main__':

    print(f'\nInvestigating repository "{repo_path}" ({branch}) from {start_date} to {end_date}')
    repo = Repository(repo_path, since=start_date, to=end_date, only_in_branch=branch)

    first_commit, last_commit = get_first_and_last_commit(repo)
    commit_count = get_commit_count(repo)
    print(f'- There are a total of {commit_count} commits.\n   - first commit: {first_commit.hash}\n   - last commit: {last_commit.hash}')

    # checkout first commit and get list of files
    files_first_commit = get_list_of_files(repo_path, first_commit.hash, ['go'])
    print(f'- # Files at first commit: {len(files_first_commit)}')

    file_dict_start = {}
    for file_name in files_first_commit:
        file_information = lizard.analyze_file(file_name)
        functions = []
        for function in file_information.function_list:
            functions.append(function.__dict__)
        file_name_without_prefix = file_name.replace(file_prefix, '')
        file_dict_start[file_name_without_prefix] = {
            'start_nloc': file_information.nloc,
            'start_token_count': file_information.token_count,
            'start_function_count': len(functions),
            'start_functions': functions
        }

    # checkout last commit and get list of files
    files_last_commit = get_list_of_files(repo_path, last_commit.hash, ['go'])
    print(f'- # Files at last commit: {len(files_last_commit)}')

    file_dict_end = {}
    for file_name in files_last_commit:
        file_information = lizard.analyze_file(file_name)
        functions = []
        for function in file_information.function_list:
            functions.append(function.__dict__)
        file_name_without_prefix = file_name.replace(file_prefix, '')
        file_dict_end[file_name_without_prefix] = {
            'end_nloc': file_information.nloc,
            'end_token_count': file_information.token_count,
            'end_function_count': len(functions),
            'end_functions': functions
        }

    # at this point we have two dictionaries 'file_dict_start' and 'file_dict_end' with static file metrics from the first
    # resp. last commit. Now we merge these two dicts together and discard all the files that were not present at the
    # start and end commit
    file_dict_combined = {}
    for file_name in file_dict_end.keys():
        if file_name not in file_dict_start:
            continue # file has been added later -> discard

        file_dict_combined[file_name] = {**file_dict_start[file_name], **file_dict_end[file_name]}
        file_dict_combined[file_name]['delta_nloc'] = file_dict_combined[file_name]['end_nloc'] - file_dict_combined[file_name]['start_nloc']
        file_dict_combined[file_name]['delta_token_count'] = file_dict_combined[file_name]['end_token_count'] - file_dict_combined[file_name]['start_token_count']
        file_dict_combined[file_name]['delta_function_count'] = file_dict_combined[file_name]['end_function_count'] - file_dict_combined[file_name]['start_function_count']
        file_dict_combined[file_name]['modification_count'] = 0 # initialise modification_count column for later use..
        file_dict_combined[file_name]['modifications'] = [] # initialise modifications column for later use..
        file_dict_combined[file_name]['coupling'] = {} # initialise coupling column for later use..

    for commit in repo.traverse_commits():
        for m in commit.modified_files:
            file_name = m.new_path
            if file_name not in file_dict_combined:
                # modified file does not exist at current commit
                continue
            # count up the modification_count counter for this file
            file_dict_combined[file_name]['modification_count'] += 1

            file_dict_combined[file_name]['modifications'].append(
                {
                    'timestamp': datetime.timestamp(commit.author_date),
                    'added_lines': m.added_lines,
                    'deleted_lines': m.deleted_lines,
                    'nloc': m.nloc,
                }
            )

            # loop over all other modified files of this commit and populate the coupling dict
            for other_m in commit.modified_files:
                other_file_name = other_m.new_path
                if file_name == other_file_name:
                    continue
                if other_file_name in file_dict_combined[file_name]['coupling']:
                    file_dict_combined[file_name]['coupling'][other_file_name] += 1
                else:
                    file_dict_combined[file_name]['coupling'][other_file_name] = 1

    # convert to dataframe and save as .csv
    df = pd.DataFrame.from_dict(file_dict_combined, orient='index')
    df.to_csv('results/file_list.csv', encoding='utf-8', index=True)

    # plotting of complexity hotspots
    max_delta_nloc = df['delta_nloc'].max()
    color_map = cm.get_cmap('cool', 12)
    colors = [color_map(0) if delta <= 0 else color_map(delta/max_delta_nloc) for delta in df['delta_nloc']]

    fig, ax = plt.subplots(figsize=(10,10))
    ax.scatter(df['end_nloc'], df['modification_count'], c=colors)
    ax.set_xlabel('end_nloc')
    ax.set_ylabel('modifications')
    ax.set_title('Complexity hotspots')
    plt.savefig('results/complexity_hotspots', bbox_inches='tight')


    # Task 1.6) ranking of complexity hotspots
    def compute_complexity(row):
        # arbitrary chosen weights for complexity metric..
        return row['end_nloc']+ row['delta_nloc'] + (row['modification_count']*20)

    df['complexity_metric'] = df.apply(lambda row: compute_complexity(row), axis=1)
    df_sorted_complexity = df.sort_values(['complexity_metric'], ascending=False)
    print('\nThis are the 10 files with the highest complexity (candidates for hotspots):')
    print(df_sorted_complexity.head(10))

    # visualize complexity trends of selected hotspot files:
    fig, axs = plt.subplots(nrows=10, ncols=1, figsize=(10, 20), sharex=True)

    counter = -1
    for ax in axs.reshape(-1):
        counter += 1
        row = df_sorted_complexity.iloc[counter]

        #x = [x['timestamp'] for x in row.modifications]
        x = [x for x in range(len(row.modifications))]
        y = [y['nloc'] for y in row.modifications]
        y_added = [y['added_lines'] for y in row.modifications]
        y_deleted = [y['deleted_lines'] for y in row.modifications]
        ax.bar(x, y_added, label='added')
        ax.bar(x, y_deleted, label='deleted', bottom=[-y for y in y_deleted])
        ax.legend()
        ax.set_title(row.name)

    plt.savefig('results/complexity_trends', bbox_inches='tight')



