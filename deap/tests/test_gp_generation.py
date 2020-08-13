import unittest
import numpy as np
from deap import gp
import time
import random


class BalancedTreeCreatorTest(unittest.TestCase):
    def test_target_lengths(self):

        cols = 1
        pset = gp.PrimitiveSet("MAIN", cols)
        pset.addPrimitive(np.add, 2, name="vadd")
        pset.addPrimitive(np.subtract, 2, name="vsub")
        pset.addPrimitive(np.multiply, 2, name="vmul")
        pset.addPrimitive(np.divide, 2, name="vdiv")
        pset.addPrimitive(np.cos, 1, name="vcos")
        pset.addPrimitive(np.sin, 1, name="vsin")
        pset.addPrimitive(np.exp, 1, name="vexp")
        pset.addPrimitive(np.log, 1, name="vlog")

        n = 1000
        min_length, max_length = 1, 100
        target_lengths = np.random.randint(1, max_length+1, n)
        biases = np.random.uniform(0, 1, n)
        trees = [ gp.generateBalanced(pset, l, bias_=b) for (l, b) in zip(target_lengths, biases) ]
        actual_lengths = np.array([len(t) for t in trees])

        self.assertTrue(np.array_equal(target_lengths, actual_lengths))


    def test_target_lengths_with_limited_pset(self):
        # we only include binary symbols in the pset to see how the 
        # tree generator deals with length values that are impossible
        # to achieve (even lengths are not possible)
        cols = 1
        pset = gp.PrimitiveSet("MAIN", cols)
        pset.addPrimitive(np.add, 2, name="vadd")
        pset.addPrimitive(np.subtract, 2, name="vsub")
        pset.addPrimitive(np.multiply, 2, name="vmul")
        pset.addPrimitive(np.divide, 2, name="vdiv")

        n = 1000
        min_length, max_length = 1, 100
        target_lengths = np.random.randint(1, max_length+1, n)
        biases = np.random.uniform(0, 1, n)
        trees = [ gp.generateBalanced(pset, l, bias_=b) for (l, b) in zip(target_lengths, biases) ]
        actual_lengths = np.array([len(t) for t in trees])
        # the generator will push the target length to an achievable value
        # in this case the value is the next odd number
        target_lengths[target_lengths % 2 == 0] += 1

        self.assertTrue(np.array_equal(target_lengths, actual_lengths))


class ProbabilisticTreeCreatorTest(unittest.TestCase):
    def test_target_lengths(self):
        min_length, max_length = 1, 100

        cols = 1
        pset = gp.PrimitiveSet("MAIN", cols)
        pset.addPrimitive(np.add, 2, name="vadd")
        pset.addPrimitive(np.subtract, 2, name="vsub")
        pset.addPrimitive(np.multiply, 2, name="vmul")
        pset.addPrimitive(np.divide, 2, name="vdiv")
        pset.addPrimitive(np.cos, 1, name="vcos")
        pset.addPrimitive(np.sin, 1, name="vsin")
        pset.addPrimitive(np.exp, 1, name="vexp")
        pset.addPrimitive(np.log, 1, name="vlog")

        n = 1000
        target_lengths = np.random.randint(1, max_length+1, n)
        biases = np.random.uniform(0, 1, n)
        trees = [ gp.generateProb(pset, l, bias_=b) for (l, b) in zip(target_lengths, biases) ]
        actual_lengths = np.array([len(t) for t in trees])

        self.assertTrue(np.array_equal(target_lengths, actual_lengths))


    def test_target_lengths_with_limited_pset(self):
        # we only include binary symbols in the pset to see how the 
        # tree generator deals with length values that are impossible
        # to achieve (even lengths are not possible)
        cols = 1
        pset = gp.PrimitiveSet("MAIN", cols)
        pset.addPrimitive(np.add, 2, name="vadd")
        pset.addPrimitive(np.subtract, 2, name="vsub")
        pset.addPrimitive(np.multiply, 2, name="vmul")
        pset.addPrimitive(np.divide, 2, name="vdiv")

        n = 1000
        min_length, max_length = 1, 100
        target_lengths = np.random.randint(1, max_length+1, n)
        biases = np.random.uniform(0, 1, n)
        trees = [ gp.generateProb(pset, l, bias_=b) for (l, b) in zip(target_lengths, biases) ]
        actual_lengths = np.array([len(t) for t in trees])
        # the generator will push the target length to an achievable value
        # in this case the value is the next odd number
        target_lengths[target_lengths % 2 == 0] += 1

        self.assertTrue(np.array_equal(target_lengths, actual_lengths))

