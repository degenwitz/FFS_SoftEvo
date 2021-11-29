from datetime import date, timedelta, datetime
import os

import pandas
from pydriller import Repository, Git
from DataCollectors.ScraperGit import Collector
from helpers import get_first_and_last_commit, get_commit_count, get_list_of_files, check_if_commit_is_fix, createConnectednessMatrix, findBiggest
import lizard
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
#plt.style.use('fivethirtyeight')

file_prefix = os.getcwd() + '/go-ipfs/'

#repo_path = 'https://github.com/ipfs/go-ipfs.git'
repo_path = 'go-ipfs'
branch = 'origin/release-v0.10.0'
start_date = datetime(2017, 10, 1)
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
        file_dict_combined[file_name]['fix_count'] = 0 # initialise fix_count column for later use..
        file_dict_combined[file_name]['modifications'] = [] # initialise modifications column for later use..
        file_dict_combined[file_name]['coupling'] = {} # initialise coupling column for later use..
        file_dict_combined[file_name]['top_logical_connection'] = ()

    for commit in repo.traverse_commits():
        # determine if commit is a fix through text analysis
        is_fix_commit = check_if_commit_is_fix(commit.msg)

        for m in commit.modified_files:
            file_name = m.new_path
            if file_name not in file_dict_combined:
                # modified file does not exist at current commit
                continue
            # count up the modification_count counter for this file
            file_dict_combined[file_name]['modification_count'] += 1

            # count up fix counter if commit message is classified as fix
            if is_fix_commit:
                file_dict_combined[file_name]['fix_count'] += 1

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


    #logical connected files detecting
    connectedGraph, dic_of_files = createConnectednessMatrix(repo, len(files_last_commit), file_dict_combined)
    res = findBiggest(connectedGraph, dic_of_files, file_dict_combined)
    candidates = []
    i_coupling = 0
    while(len(candidates) < 10):
        file = res[-1*i_coupling]
        try:
            if file_dict_combined[file[0]]['modification_count'] > 4:
                candidates.append(file)
        except:
            pass
        i_coupling += 1
    x_achse =  [x[2]*100 for x in candidates]
    y_achse = [x[3]*100 for x in candidates]
    print(candidates)
    color = np.random.rand(10)
    fig, ax = plt.subplots(figsize=(10,10))
    df = pandas.DataFrame({
        'X':x_achse,
        'Y':y_achse,
        'Colors': color,
        'bubble size': np.ones(10)*300
    })
    plt.scatter('X','Y', data=df)
    plt.scatter('X', 'Y', data=df)
    plt.xlabel("Percentage of commits of a that change a and b", size=16)
    plt.ylabel("Percentage of commits of b that change a and b", size=16)
    plt.title("logical coupling hotspot candidates", size=18)

    plt.savefig('results/complexity_cupling', bbox_inches='tight')



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
        return row['end_nloc'] + (row['delta_nloc']*3) + (row['modification_count']*20)

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


    # plot defective hotspots (bar chart)
    df_sorted_fix_count = df.sort_values(['fix_count'], ascending=False)
    top_ten = df_sorted_fix_count.head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(top_ten.index, top_ten['fix_count'])
    plt.xticks(rotation=90)
    ax.set_title('defective hotspots')
    plt.savefig('results/defective_hotspots', bbox_inches='tight')

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(df['start_nloc'], df['fix_count'])
    ax.set_xlabel('complexity (lines of code)')
    ax.set_ylabel('defectivity (fix modifications)')
    ax.set_title('Defectivity and Complexity correlation')
    plt.savefig('results/correlation', bbox_inches='tight')



