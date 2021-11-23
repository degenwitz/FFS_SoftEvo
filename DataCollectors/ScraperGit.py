from pydriller.metrics.process.lines_count import LinesCount

class Collector:

    def __init__(self, repo):
        self.__repo = repo

    def getLineChanges(self, beg, end):
        metric = LinesCount(path_to_repo=self.__repo,
                            from_commit=beg,
                            to_commit=end)
        added_count = metric.count_added()
        added_max = metric.max_added()
        added_avg = metric.avg_added()
        print('Total lines added per file: {}'.format(added_count))
        print('Maximum lines added per file: {}'.format(added_max))
        print('Average lines added per file: {}'.format(added_avg))
