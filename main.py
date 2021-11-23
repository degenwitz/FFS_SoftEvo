from datetime import date, timedelta, datetime

from pydriller import Repository

from DataCollectors.ScraperGit import Collector

repo = 'https://github.com/ipfs/go-ipfs.git'

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    a = Collector(repo)
    intervals = a.getHashesForTimePeriods(datetime(2018,1,1), datetime.today(),timedelta(weeks=2))
    print(intervals)
    beg = '64b532fbb14145557dda7cb7986daea1e156f76d'
    end = '0c2f9d5950c4245d89fcaf39dd1baa754587231b'
    b = a.getLineChanges(beg, end)
    c = a.parseByFolder(b)
    c = c['core']
    for subdic in c:
        if type(c[subdic]) == dict:
            print(subdic, a.linesChangedInFolder(c[subdic]),'-------------------------------')
            for subsubdic in c[subdic]:
                if type(c[subdic][subsubdic]) == dict:
                    print(subsubdic, a.linesChangedInFolder(c[subdic][subsubdic]))


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
