from pydriller import Repository

from DataCollectors.ScraperGit import Collector

repo = 'https://github.com/ipfs/go-ipfs.git'

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    beg = '64b532fbb14145557dda7cb7986daea1e156f76d'
    end = '0c2f9d5950c4245d89fcaf39dd1baa754587231b'
    a = Collector(repo)
    b = a.getLineChanges(beg, end)
    c = a.parseByFolder(b)
    for subdic in c:
        if type(c[subdic]) == dict:
            print(subdic, a.linesChangedInFolder(c[subdic]))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
