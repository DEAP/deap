import unittest

import numpy

from deap import tools


class LogbookTest(unittest.TestCase):
    def test_compile(self):
        s = tools.Statistics()
        s.register("mean", numpy.mean)
        s.register("max", max)
        res = s.compile([1, 2, 3, 4])
        self.assertDictEqual(res, {'max': 4, 'mean': 2.5})

        res = s.compile([5, 6, 7, 8])
        self.assertDictEqual(res, {'mean': 6.5, 'max': 8})
