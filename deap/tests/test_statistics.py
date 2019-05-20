from operator import itemgetter
import unittest

import numpy

from deap import tools


class LogbookTest(unittest.TestCase):
    def test_statistics_compile(self):
        s = tools.Statistics()
        s.register("mean", numpy.mean)
        s.register("max", max)
        res = s.compile([1, 2, 3, 4])
        self.assertDictEqual(res, {'max': 4, 'mean': 2.5})

        res = s.compile([5, 6, 7, 8])
        self.assertDictEqual(res, {'mean': 6.5, 'max': 8})

    def test_multi_statistics_compile(self):
        len_stats = tools.Statistics(key=len)
        itm0_stats = tools.Statistics(key=itemgetter(0))
        mstats = tools.MultiStatistics(length=len_stats, item=itm0_stats)
        mstats.register("mean", numpy.mean, axis=0)
        mstats.register("max", numpy.max, axis=0)
        res = mstats.compile([[0.0, 1.0, 1.0, 5.0], [2.0, 5.0]])
        self.assertDictEqual(res, {'length': {'mean': 3.0, 'max': 4}, 'item': {'mean': 1.0, 'max': 2.0}})
