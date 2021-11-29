from datetime import date, timedelta, datetime
import os
from pydriller import Repository, Git
import lizard
import pandas as pd
from scipy.sparse import lil_matrix
import numpy as np

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

def createConnectednessMatrix(repo, amountOfFiles, file_dict_combined):
    connectedGraph = np.zeros((amountOfFiles, amountOfFiles),
                          dtype = np.float)
    dic_of_files = {}
    counter_of_dic = 0
    for commit in repo.traverse_commits():
        modified_files = []
        for file in commit.modified_files:
            file_name = (file.old_path if file.old_path!=None  else file.new_path)
            if ".go" in file_name and file_name in file_dict_combined:
                if(file_name not in dic_of_files):
                    dic_of_files[file_name] = counter_of_dic
                    counter_of_dic += 1
                modified_files.append(dic_of_files[file_name])
        for file_a in modified_files:
            for file_b in modified_files:
                connectedGraph[file_a,file_b] += 1;
    for i in range(0,amountOfFiles):
        total_commits = connectedGraph[i,i]
        if(total_commits) > 0:
            for j in range(0,amountOfFiles):
                connectedGraph[i,j] /= total_commits
    return (connectedGraph, dic_of_files)

def findBiggest(connectedGrap, dic_of_files, file_dict_combined):
    list_of_results = []
    for file_name in dic_of_files:
        number_of_file = dic_of_files[file_name]
        connectedGrap[number_of_file, number_of_file] = 0
        row = connectedGrap[number_of_file]
        try:
            index_max = row.argmax()
            value_max = row[index_max]
            key_list = list(dic_of_files.keys())
            val_list = list(dic_of_files.values())
            pos = val_list.index(index_max)
            file_name_max = key_list[pos]
            list_of_results.append((file_name, file_name_max, value_max, connectedGrap[pos][number_of_file]))
            file_dict_combined[file_name]['top_logical_connection'] = (file_name_max, value_max, connectedGrap[pos][number_of_file])
        except:
            pass
    return sorted(list_of_results, key=lambda x:x[2])
    
def check_if_commit_is_fix(msg):
    # Note: this can be improved, at the moment it is very trivial
    words = msg.replace('(', ' ').lower().split(' ')
    if 'fix' in words or 'fix:' in words:
        return True
    else:
        return False

