# To change this template, choose Tools | Templates
# and open the template in the editor.

import unittest

import random
import eap.base as base
import eap.toolbox as toolbox


class  TestCrossovers(unittest.TestCase):
    def setUp(self):
        random.seed(0)
        self.Ind1 = base.ListIndividual(size=5, generator=base.indiceGenerator(5),
                                        fitness=base.Fitness)
        self.Ind2 = base.ListIndividual(size=5, generator=base.indiceGenerator(5),
                                        fitness=base.Fitness)
    

    def testTwoPointsCrossover(self):
        expectedChild1 = [2, 0, 1, 1, 4]
        expectedChild2 = [3, 0, 4, 3, 2]
        child1, child2 = toolbox.twoPointsCx(self.Ind1, self.Ind2)
        self.assertEquals(child1, expectedChild1)
        self.assertEquals(child2, expectedChild2)


    def testOnePointCrossover(self):
        expectedChild1 = [2, 0, 4, 1, 2]
        expectedChild2 = [3, 0, 1, 3, 4]
        child1, child2 = toolbox.onePointCx(self.Ind1, self.Ind2)
        self.assertEquals(child1, expectedChild1)
        self.assertEquals(child2, expectedChild2)


    def testPMXCrossover(self):
        expectedChild1 = [2, 0, 4, 3, 1]
        expectedChild2 = [3, 0, 1, 4, 2]
        child1, child2 = toolbox.pmxCx(self.Ind1, self.Ind2)
        self.assertEquals(child1, expectedChild1)
        self.assertEquals(child2, expectedChild2)


class TestMutations(unittest.TestCase):
    def setUp(self):
        random.seed(0)
        self.RealInd = base.ListIndividual(size=5, generator=base.realGenerator(),
                                        fitness=base.Fitness)
        self.BoolInd = base.ListIndividual(size=5, generator=base.booleanGenerator(),
                                        fitness=base.Fitness)


    def testFilpBitMutation(self):
        expectedMutant = [False, True, True, False, True]
        mutant = toolbox.flipBitMut(self.BoolInd, flipIndxPb=0.5)
        self.assertEquals(mutant, expectedMutant)


    def testShuffleIndexesMutation(self):
        expectedMutant = [False, True, True, False, False]
        mutant = toolbox.shuffleIndxMut(self.BoolInd, shuffleIndxPb=0.5)
        self.assertEquals(mutant, expectedMutant)


    def testGaussianMutation(self):
        expectedMutant = [0.84442185152504812, 0.75795440294030247,
                          1.445875763057654, 0.56536772757640075, 0.51127472136860852]
        mutant = toolbox.gaussMut(self.RealInd, mu=1, sigma=0.5, mutIndxPb=0.5)
        self.assertEquals(mutant, expectedMutant)


class TestAlgorithms(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()

