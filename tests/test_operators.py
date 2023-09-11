import unittest
from unittest import mock
import random
import operator
import math
import copy

from deap.tools import crossover
from deap import gp


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

class TestGpCxUniform(unittest.TestCase):
    def setUp(self):
        self.pset = gp.PrimitiveSet("MAIN", 2)
        self.pset.addPrimitive(operator.add, 2)
        self.pset.addPrimitive(operator.sub, 2)
        self.pset.addPrimitive(operator.mul, 2)
        self.pset.addPrimitive(math.cos, 1)
        self.pset.addPrimitive(math.sin, 1)
        self.pset.addTerminal(5)
    
    def tearDown(self):
        del self.pset
    
    def test_no_changes_when_zero_swap_prob(self):
        expr1 = 'sub(add(ARG0, ARG0), add(5, sub(ARG0, 5)))'
        parent1 = gp.PrimitiveTree.from_string(string=expr1, pset=self.pset)

        expr2 = 'cos(sin(add(5, ARG0)))'
        parent2 = gp.PrimitiveTree.from_string(string=expr2, pset=self.pset)

        child1, child2 = gp.cxUniform(parent1, parent2, swap_prob=0.0)

        self.assertEqual(expr1, str(child1))
        self.assertEqual(expr2, str(child2))

    def test_no_change_when_one_has_only_one_node(self):
        expr1 = 'sub(add(ARG0, ARG0), add(5, sub(ARG0, 5)))'
        parent1 = gp.PrimitiveTree.from_string(string=expr1, pset=self.pset)

        expr2 = 'ARG0'
        parent2 = gp.PrimitiveTree.from_string(string=expr2, pset=self.pset)

        child1, child2 = gp.cxUniform(parent1, parent2, swap_prob=1.0)

        self.assertEqual(expr1, str(child1))
        self.assertEqual(expr2, str(child2))
    
    def test_same_results_on_equal_expressions(self):
        expr1 = 'sub(add(ARG0, ARG0), add(5, sub(ARG0, 5)))'
        parent1 = gp.PrimitiveTree.from_string(string=expr1, pset=self.pset)

        expr2 = 'sub(add(ARG0, ARG0), add(5, sub(ARG0, 5)))'
        parent2 = gp.PrimitiveTree.from_string(string=expr2, pset=self.pset)

        child1, child2 = gp.cxUniform(parent1, parent2, swap_prob=1.0)

        self.assertEqual(expr1, str(child1))
        self.assertEqual(expr2, str(child2))

    def test_roots_remains_the_same(self):
        expr1 = 'sub(add(ARG0, ARG0), add(5, sub(ARG0, 5)))'
        parent1 = gp.PrimitiveTree.from_string(string=expr1, pset=self.pset)

        expr2 = 'sin(add(ARG0, ARG0))'
        parent2 = gp.PrimitiveTree.from_string(string=expr2, pset=self.pset)

        child1, child2 = gp.cxUniform(
            copy.deepcopy(parent1),
            copy.deepcopy(parent2),
            swap_prob=1.0)

        self.assertEqual(parent1.root, child1.root)
        self.assertEqual(parent2.root, child2.root)

    def test_correctness1(self):
        expr1 = 'sub(add(ARG0, ARG0), add(5, sub(ARG0, 5)))'
        parent1 = gp.PrimitiveTree.from_string(string=expr1, pset=self.pset)

        expr2 = 'cos(sin(add(5, ARG0)))'
        parent2 = gp.PrimitiveTree.from_string(string=expr2, pset=self.pset)

        child1, child2 = gp.cxUniform(parent1, parent2, swap_prob=1.0)

        self.assertEqual(str(child1), 'sub(sin(ARG0), add(5, sub(ARG0, 5)))')
        self.assertEqual(str(child2), 'cos(add(add(5, ARG0), ARG0))')

    def test_correctness2(self):
        def add3(x, y, z):
            return x + y + z
        self.pset.addPrimitive(add3, arity=3)

        expr1 = 'mul(sin(add3(ARG0, ARG0, 5)), add3(sin(5), cos(ARG0), mul(ARG0, ARG0)))'
        parent1 = gp.PrimitiveTree.from_string(string=expr1, pset=self.pset)

        expr2 = 'add3(5, ARG0, ARG0)'
        parent2 = gp.PrimitiveTree.from_string(string=expr2, pset=self.pset)

        child1, child2 = gp.cxUniform(parent1, parent2, swap_prob=1.0)

        self.assertEqual(str(child1), 'mul(5, ARG0)')
        self.assertEqual(str(child2), 'add3(sin(add3(ARG0, ARG0, 5)), add3(sin(5), cos(ARG0), mul(ARG0, ARG0)), ARG0)')

    @mock.patch("random.random")
    def test_correctness3(self, mock_random):
        mock_random.side_effect = [0.4, 0.6, 0.4, 0.0, 0.7, 0.9, 0.2, 0.8]
        expr1 = 'sub(add(ARG0, ARG0), add(5, sub(ARG0, 5)))'
        parent1 = gp.PrimitiveTree.from_string(string=expr1, pset=self.pset)

        expr2 = 'add(sub(5, 5), sub(ARG0, mul(5, ARG0)))'
        parent2 = gp.PrimitiveTree.from_string(string=expr2, pset=self.pset)

        child1, child2 = gp.cxUniform(parent1, parent2, swap_prob=0.5)

        self.assertEqual(str(child1), 'sub(add(ARG0, 5), sub(5, sub(5, ARG0)))')
        self.assertEqual(str(child2), 'add(sub(5, ARG0), add(ARG0, mul(ARG0, 5)))')

