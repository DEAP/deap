#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

import sys
import os

sys.path.append(os.path.abspath('..'))

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.operators as operators
import pickle
import random

# gr*.pickle contains the numpy ndarray of the distance map
# Optimal solutions are : gr17 = 2085, gr24 = 1272, gr120 = 6942
lDistanceFile = open('gr24.pickle', 'r')
lDistanceMap = pickle.load(lDistanceFile)
lDistanceFile.close()
lIndSize = lDistanceMap.shape[0]

random.seed(1024)

lCreator = creator.Creator()

lCreator.define('crtFitness', base.Fitness)
lCreator.define('crtIndividual', base.Individual, size=lIndSize,
                generator=base.indiceGenerator(lIndSize), fitness=lCreator.crtFitness)
lCreator.define('crtPopulation', base.Population, size=400,
                generator=lCreator.crtIndividual)

def evalTSP(individual):
    if not individual.mFitness.isValid():
        lDistance = 0
        for lGene1, lGene2 in zip(individual[:], individual[1:-1]):
            lDistance += lDistanceMap[lGene1, lGene2]
        individual.mFitness.append(lDistance)

# Instanciate a toolbox that will contain the operators
lToolbox = toolbox.Toolbox()
# Add a partialy matched crossover method to the toolbox
lToolbox.register('crossover', operators.pmxCx)
# Add a shuffle indice mutation method to the toolbox with each index having a
# probability of 5% to be moved
lToolbox.register('mutate', operators.shuffleIndxMut, shuffleIndxPb=0.05)
# Add a tournament selection method to the toolbox with tournament size of 3
lToolbox.register('select', operators.tournSel, tournSize=3)

lPop = lCreator.crtPopulation()

map(evalTSP, lPop)

CXPB = 0.5
MUTPB = 0.2

for g in range(100):
    print 'Generation', g

    lPop[:] = lToolbox.select(lPop, n=len(lPop), tournSize=3)

    lMateIndx = []
    lMutateIndx = []

    for lIndx in xrange(len(lPop)):
        if random.random() < CXPB:
            lMateIndx.append(lIndx)
        if random.random() < MUTPB:
            lMutateIndx.append(lIndx)

    # Apply crossover on the choosen indexes and replace parents
    for i, j in zip(lMateIndx[::2], lMateIndx[1::2]):
        lPop[i], lPop[j] = lToolbox.crossover(lPop[i], lPop[j])
    # Apply mutation on the choosen indexes and replace parents
    for i in lMutateIndx:
        lPop[i] = lToolbox.mutate(lPop[i])

    map(evalTSP, lPop)

    # Gather all the fitnesses in one list and print the stats
    lFitnesses = [lInd.mFitness[0] for lInd in lPop]
    print '\tMinimum :', min(lFitnesses)
    print '\tMaximum :', max(lFitnesses)
    print '\tAverage :', sum(lFitnesses)/len(lFitnesses)

print 'End of evolution'
#print lStats.getStats('bestIndividualHistory')