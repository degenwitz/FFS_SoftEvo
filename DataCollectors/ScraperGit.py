from pydriller.metrics.process.lines_count import LinesCount

class Collector:

    def __init__(self, repo):
        self.__repo = repo

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
