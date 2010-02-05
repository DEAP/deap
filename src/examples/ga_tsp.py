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
import eap.toolbox as toolbox
import eap.algorithms as algorithms
import pickle

# gr*.pickle contains the numpy ndarray of the distance map
# Optimal solutions are : gr17 = 2085, gr24 = 1272, gr120 = 6942
lDistanceFile = open('gr17.pickle', 'r')
lDistanceMap = pickle.load(lDistanceFile)
lDistanceFile.close()
lIndSize = lDistanceMap.shape[0]

print lDistanceMap

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness)
lTools.register('individual', base.Individual, size=lIndSize,
                generator=base.indiceGenerator(lIndSize), fitness=lTools.fitness)
lTools.register('population', base.Population, size=400,
                generator=lTools.individual)

def evalTSP(individual):
    if not individual.mFitness.isValid():
        lDistance = lDistanceMap[individual[-1], individual[0]]
        for lGene1, lGene2 in zip(individual[0:-1], individual[1:]):
            lDistance += lDistanceMap[lGene1, lGene2]
        individual.mFitness.append(lDistance)

lTools.register('crossover', toolbox.pmCx)
lTools.register('mutate', toolbox.shuffleIndxMut, shuffleIndxPb=0.05)
lTools.register('select', toolbox.tournSel, tournSize=3)
lTools.register('evaluate', evalTSP)

lPop = lTools.population()

algorithms.simpleGA(lTools, lPop, 0.5, 0.2, 100)

lBest = lPop[0]
for lInd in lPop[1:]:
    if lInd.mFitness > lBest.mFitness:
        lBest = lInd

print lInd
