import unittest
from unittest import mock
import random

from deap.tools import crossover


class TestCxOrdered(unittest.TestCase):
    def setUp(self):
        pass

    def test_crossover(self):
        a = [8, 7, 3, 4, 5, 6, 0, 2, 1, 9]
        b = [7, 6, 0, 1, 2, 9, 8, 4, 3, 5]
        expected_ap = [4, 5, 6, 1, 2, 9, 0, 8, 7, 3]
        expected_bp = [1, 2, 9, 4, 5, 6, 8, 3, 7, 0]

        with mock.patch("random.sample", return_value=[3, 5]):
            ap, bp = crossover.cxOrdered(a, b)

            self.assertSequenceEqual(expected_ap, ap)
            self.assertSequenceEqual(expected_bp, bp)

    def test_crossover_identical(self):
        i1 = list(range(100))
        random.shuffle(i1)
        i2 = list(range(100))
        random.shuffle(i2)

        a, b = sorted(random.sample(range(len(i1)), 2))

        with mock.patch("random.sample", return_value=[a, b]):
            ap, bp = crossover.cxOrdered(i1, i2)

        self.assertSequenceEqual(sorted(ap), list(range(len(ap))))
        self.assertSequenceEqual(sorted(bp), list(range(len(bp))))
