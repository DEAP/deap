# To change this template, choose Tools | Templates
# and open the template in the editor.

import unittest

import random
import eap.toolbox as toolbox


class  TestCrossovers(unittest.TestCase):
    def setUp(self):
        random.seed(0)
        self.Ind1 = [2, 0, 1, 3, 4]
        self.Ind2 = [3, 0, 4, 1, 2]
        self.Ind1Ref = [2, 0, 1, 3, 4]
        self.Ind2Ref = [3, 0, 4, 1, 2]


    def testTwoPointsCrossover(self):
        expectedChild1 = [2, 0, 1, 3, 2]
        expectedChild2 = [3, 0, 4, 1, 4]
        child1, child2 = toolbox.twoPointsCx(self.Ind1, self.Ind2)
        self.assertEquals(child1, expectedChild1)
        self.assertEquals(child2, expectedChild2)
        self.assertEquals(self.Ind1, self.Ind1Ref)
        self.assertEquals(self.Ind2, self.Ind2Ref)

    def testOnePointCrossover(self):
        expectedChild1 = [2, 0, 1, 3, 2]
        expectedChild2 = [3, 0, 4, 1, 4]
        child1, child2 = toolbox.onePointCx(self.Ind1, self.Ind2)
        self.assertEquals(child1, expectedChild1)
        self.assertEquals(child2, expectedChild2)
        self.assertEquals(self.Ind1, self.Ind1Ref)
        self.assertEquals(self.Ind2, self.Ind2Ref)

    def testPMXCrossover(self):
        expectedChild1 = [4, 0, 3, 1, 2]
        expectedChild2 = [1, 0, 2, 3, 4]
        child1, child2 = toolbox.pmCx(self.Ind1, self.Ind2)
        self.assertEquals(child1, expectedChild1)
        self.assertEquals(child2, expectedChild2)
        self.assertEquals(self.Ind1, self.Ind1Ref)
        self.assertEquals(self.Ind2, self.Ind2Ref)

class TestMutations(unittest.TestCase):
    def setUp(self):
        random.seed(0)
        self.RealIndRef = [0, 0, 0, 0, 0]
        self.BoolIndRef = [True, True, False, False, True]
        self.RealInd = [0, 0, 0, 0, 0]
        self.BoolInd = [True, True, False, False, True]

    def testFilpBitMutation(self):
        expectedMutant = [True, True, True, True, True]
        mutant = toolbox.flipBitMut(self.BoolInd, flipIndxPb=0.5)
        self.assertEquals(mutant, expectedMutant)
        self.assertEquals(self.BoolInd, self.BoolIndRef)

    def testShuffleIndexesMutation(self):
        expectedMutant = [True, False, True, True, False]
        mutant = toolbox.shuffleIndxMut(self.BoolInd, shuffleIndxPb=0.5)
        self.assertEquals(mutant, expectedMutant)
        self.assertEquals(self.BoolInd, self.BoolIndRef)

    def testGaussianMutation(self):
        expectedMutant = [0, 0, -0.033503257864528985, 0.59737333937499937, 0]
        mutant = toolbox.gaussMut(self.RealInd, mu=0, sigma=0.5, mutIndxPb=0.5, min=-1, max=1)
        self.assertEquals(mutant, expectedMutant)
        self.assertEquals(self.RealInd, self.RealIndRef)

class TestAlgorithms(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()

