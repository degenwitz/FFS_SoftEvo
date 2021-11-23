from pydriller import Repository
from pydriller.metrics.process.lines_count import LinesCount

class Collector:

    def __init__(self, repo):
        self.__repo = repo

    def getHashesForTimePeriods(self, start, end, periode):
        hashes = []
        currentEnd = start+periode
        strt = None
        nd = None
        last = None
        for commit in Repository(self.__repo).traverse_commits():
            a = commit.committer_date
            if(a.timestamp() < start.timestamp() ):
                continue
            elif(a.timestamp() > end.timestamp()):
                break
            else:
                if strt == None:
                    strt = commit
                if a.timestamp() > currentEnd.timestamp():
                    nd = last
                    hashes.append((strt.hash,nd.hash))
                    start = a
                    currentEnd += periode
            last = commit
        return hashes


    def getLineChanges(self, beg, end):
        metric = LinesCount(path_to_repo=self.__repo,
                            from_commit=beg,
                            to_commit=end)
        added_count = metric.count_added()
        return added_count

    def parseByFolder(self, originalCount):
        dic = {}
        for name in originalCount:
            if(name == None):
                continue
            if '/' in name:
                parent = name[:name.find('/')]
                child = name[name.find('/')+1:]
                if parent not in dic:
                    dic[parent] = {}
                dic[parent][child] = originalCount[name]
                dic[parent] = self.parseByFolder(dic[parent])
            else:
                dic[name] = originalCount[name]
        return dic

    def linesChangedInFolder(self, parsedFolder):
        count = 0
        for entry in parsedFolder.values():
            if type(entry) == dict:
                count += self.linesChangedInFolder(entry)
            else:
                count += entry
        return count
