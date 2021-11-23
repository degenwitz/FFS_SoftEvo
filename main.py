from DataCollectors.ScraperGit import Collector

repo = 'https://github.com/ipfs/go-ipfs.git'

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    for commit in Repository('path/to/the/repo').traverse_commits():
        print(
            'The commit {} has been modified by {}, '
            'committed by {} in date {}'.format(
                commit.hash,
                commit.author.name,
                commit.committer.name,
                commit.committer_date
            )
        )
    print_hi('PyCharm')
    a = Collector(repo)
    a.getLineChanges()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
