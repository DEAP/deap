from functools import partial
import random
import unittest

from deap import tools


class LogbookTest(unittest.TestCase):
    def test_statistics_compile(self):
        l = 10
        gen_idx = partial(random.sample, list(range(l)), l)
        i = tools.initIterate(list, gen_idx)
        self.assertSetEqual(set(i), set(range(l)))
