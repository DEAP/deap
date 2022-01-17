import unittest

import numpy

from deap.base import Fitness


MAX = Fitness.MAXIMIZE
MIN = Fitness.MINIMIZE


class TestBaseFitness(unittest.TestCase):
    def test_is_greater_maximize_single_value(self):
        f1 = Fitness(MAX, 3)
        f2 = Fitness(MAX, 0)
        self.assertGreater(f1, f2)

    def test_is_less_maximize_single_value(self):
        f1 = Fitness(MAX, 3)
        f2 = Fitness(MAX, 0)
        self.assertLess(f2, f1)

    def test_is_equal_maximize_single_value(self):
        f1 = Fitness(MAX, 3)
        f2 = Fitness(MAX, 3)
        self.assertEqual(f1, f2)

    def test_is_greater_minimize_single_value(self):
        f1 = Fitness(MIN, 0)
        f2 = Fitness(MIN, 3)
        self.assertGreater(f1, f2)

    def test_is_less_minimize_single_value(self):
        f1 = Fitness(MIN, 0)
        f2 = Fitness(MIN, 3)
        self.assertLess(f2, f1)

    def test_is_equal_minimize_single_value(self):
        f1 = Fitness(MIN, 3)
        f2 = Fitness(MIN, 3)
        self.assertEqual(f1, f2)

    def test_dominates_multi_value(self):
        f1 = Fitness((MAX, MAX), (3, 3))
        f2 = Fitness((MAX, MAX), (0, 0))
        self.assertGreater(f1, f2)

    def test_is_dominated_multi_value(self):
        f1 = Fitness((MAX, MAX), (3, 3))
        f2 = Fitness((MAX, MAX), (0, 0))
        self.assertLess(f2, f1)

    def test_equal_multi_value_different(self):
        f1 = Fitness((MAX, MAX), (3, 3))
        f2 = Fitness((MAX, MAX), (2, 4))
        self.assertEqual(f1, f2)

    def test_equal_multi_value_same(self):
        f1 = Fitness((MAX, MAX), (3, 3))
        f2 = Fitness((MAX, MAX), (3, 3))
        self.assertEqual(f1, f2)

    def test_different_len_raises(self):
        self.assertRaises(ValueError, Fitness, (MAX, MAX), 1)
        self.assertRaises(ValueError, Fitness, MAX, (1, 1))

    def test_string_initvalue_fails(self):
        self.assertRaises(ValueError, Fitness, MAX, "z")

    def test_string_number_initvalue(self):
        f = Fitness(MAX, "3")
        self.assertEqual(f.value, 3)

    def test_string_numbers_initvalue(self):
        f = Fitness(MAX, "33")
        self.assertEqual(f.value, 33)

    def test_none_initvalue(self):
        f = Fitness(MAX, None)
        self.assertFalse(f.evaluated)
        self.assertFalse(f.valid)

    def test_no_initvalue_invalid(self):
        f = Fitness(MAX)
        self.assertFalse(f.valid)

    def test_no_initvalue_not_evaluated(self):
        f = Fitness(MAX)
        self.assertFalse(f.evaluated)

    def test_no_multi_initvalue_invalid(self):
        f = Fitness((MAX, MAX))
        self.assertFalse(f.valid)

    def test_no_multi_initvalue_not_evaluated(self):
        f = Fitness((MAX, MAX))
        self.assertFalse(f.evaluated)

    def test_single_value_valid(self):
        f = Fitness(MAX, 3)
        self.assertTrue(f.valid)

    def test_single_value_evaluated(self):
        f = Fitness(MAX, 3)
        self.assertTrue(f.evaluated)

    def test_multi_value_valid(self):
        f = Fitness((MAX, MAX), (3, 3))
        self.assertTrue(f.valid)

    def test_multi_value_evaluated(self):
        f = Fitness((MAX, MAX), (3, 3))
        self.assertTrue(f.evaluated)

    def test_setget_value_single_value(self):
        value = 3
        f = Fitness(MAX)
        f.value = value
        self.assertEqual(f.value, value)

    def test_setget_value_single_tuple_value(self):
        value = (3,)
        f = Fitness(MAX)
        f.value = value
        self.assertEqual(f.value, value)

    def test_setget_value_mutli_value(self):
        value = (3, 3)
        f = Fitness((MAX, MAX))
        f.value = value
        numpy.testing.assert_array_equal(f.value, value)

    def test_deleted_single_value_invalid(self):
        f = Fitness(MAX, 3)
        del f.value
        self.assertFalse(f.valid)

    def test_deleted_single_value_not_evaluated(self):
        f = Fitness(MAX, 3)
        del f.value
        self.assertFalse(f.evaluated)

    def test_deleted_multi_value_invalid(self):
        f = Fitness((MAX, MAX), (3, 3))
        del f.value
        self.assertFalse(f.valid)

    def test_deleted_multi_value_not_evaluated(self):
        f = Fitness((MAX, MAX), (3, 3))
        del f.value
        self.assertFalse(f.evaluated)

    def test_is_greater_maximize_single_value_constraint_violated(self):
        f1 = Fitness(MAX, 0, [False])
        f2 = Fitness(MAX, 3, [True])
        self.assertGreater(f1, f2)

    def test_is_less_maximize_single_value_constraint_violated(self):
        f1 = Fitness(MAX, 3, [True])
        f2 = Fitness(MAX, 0, [False])
        self.assertLess(f1, f2)

    def test_is_equal_maximize_single_value_constraint_violated(self):
        f1 = Fitness(MAX, 3, [True])
        f2 = Fitness(MAX, 3, [True])
        self.assertEqual(f1, f2)

    def test_is_equal_maximize_single_value_constraint_not_violated(self):
        f1 = Fitness(MAX, 3, [False])
        f2 = Fitness(MAX, 3, [False])
        self.assertEqual(f1, f2)

    def test_is_greater_maximize_multi_value_constraint_violated(self):
        f1 = Fitness((MAX, MAX), (0, 0), [False])
        f2 = Fitness((MAX, MAX), (3, 3), [True])
        self.assertGreater(f1, f2)

    def test_is_less_maximize_multi_value_constraint_violated(self):
        f1 = Fitness((MAX, MAX), (3, 3), [True])
        f2 = Fitness((MAX, MAX), (0, 0), [False])
        self.assertLess(f1, f2)

    def test_is_equal_maximize_multi_value_constraint_violated(self):
        f1 = Fitness((MAX, MAX), (3, 3), [True])
        f2 = Fitness((MAX, MAX), (3, 3), [True])
        self.assertEqual(f1, f2)

    def test_is_equal_maximize_multi_value_constraint_not_violated(self):
        f1 = Fitness((MAX, MAX), (3, 3), [False])
        f2 = Fitness((MAX, MAX), (3, 3), [False])
        self.assertEqual(f1, f2)
