
import itertools
import unittest
from unittest import mock

import numpy

from deap import algorithms, base


class Ind(list):
    def __init__(self, content):
        super().__init__(content)
        self.fitness = mock.Mock()


class TestVariations(unittest.TestCase):
    def setUp(self):
        self.cx_mock = mock.Mock(side_effect=lambda i1, i2: (i1, i2))
        self.mut_mock = mock.Mock(side_effect=lambda i: (i,))
        self.tb = base.Toolbox()
        self.tb.register("mate", self.cx_mock)
        self.tb.register("mutate", self.mut_mock)

    def test_and_var_all_deepcopies(self):
        pop = [Ind(range(i, i + 4)) for i in range(5)] * 2
        res = itertools.islice(algorithms.and_variation(pop, self.tb, 1.0, 1.0), 15)

        for i1, i2 in itertools.combinations(res, 2):
            self.assertIsNot(i1, i2)

    def test_and_var_calls(self):
        pop = [Ind(range(i, i + 4)) for i in range(5)] * 2

        mu = 10
        list(itertools.islice(algorithms.and_variation(pop, self.tb, 1.0, 1.0), mu))

        self.assertEqual(self.cx_mock.call_count, mu // 2)
        self.assertEqual(self.mut_mock.call_count, mu)

        self.cx_mock.reset_mock()
        self.mut_mock.reset_mock()

        mu = 11
        list(itertools.islice(algorithms.and_variation(pop, self.tb, 1.0, 1.0), mu))

        self.assertEqual(self.cx_mock.call_count, (mu // 2) + 1)
        self.assertEqual(self.mut_mock.call_count, mu + 1)

    def test_or_var_all_deepcopies(self):
        pop = [Ind(range(i, i + 4)) for i in range(5)] * 2
        res = itertools.islice(algorithms.or_variation(pop, self.tb, 0.33, 0.33), 15)

        for i1, i2 in itertools.combinations(res, 2):
            self.assertIsNot(i1, i2)

    def test_or_var_asserts(self):
        self.assertRaises(AssertionError,
                          iter(algorithms.or_variation([], None, 1.0, 1.0)).__next__)

    def test_or_var_calls(self):
        pop = [Ind(range(i, i + 4)) for i in range(5)] * 2

        mu = 10
        list(itertools.islice(algorithms.or_variation(pop, self.tb, 1.0, 0.0), mu))

        self.assertEqual(self.cx_mock.call_count, mu)
        self.assertEqual(self.mut_mock.call_count, 0)

        self.cx_mock.reset_mock()
        self.mut_mock.reset_mock()

        list(itertools.islice(algorithms.or_variation(pop, self.tb, 0.0, 1.0), mu))

        self.assertEqual(self.cx_mock.call_count, 0)
        self.assertEqual(self.mut_mock.call_count, mu)


class TestAlgorithms(unittest.TestCase):
    def setUp(self):
        self.sel_mock = mock.Mock(side_effect=lambda p, k: list(itertools.islice(itertools.cycle(p), k)))
        self.eval_mock = mock.Mock()
        self.tb = base.Toolbox()
        self.tb.register("select", self.sel_mock)
        self.tb.register("evaluate", self.eval_mock)

    def test_simple_algorithm_population_updated(self):
        pop = [Ind([0] * 4) for i in range(5)]

        with mock.patch("deap.algorithms.and_variation") as mock_var, \
                mock.patch("deap.algorithms._evaluate_invalids") as mock_eval_invld:
            mock_var.return_value = itertools.repeat([1] * 4)

            state = next(algorithms.SimpleAlgorithm(pop, self.tb, 1.0, 1.0))

            self.assertEqual(mock_var.call_count, 1)
            self.assertEqual(mock_eval_invld.call_count, 1)
            self.assertTrue(numpy.allclose(state.population, 1))
            self.assertNotEqual(pop, state.population)
