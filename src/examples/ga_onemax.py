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

import random

import eap.base as base
import eap.toolbox as toolbox

random.seed(64)

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(1.0,))
lTools.register('individual', base.Individual, size=100,
                fitness=lTools.fitness, generator=base.booleanGenerator())
lTools.register('population', base.Population, size=300,
                generator=lTools.individual)

def evalOneMax(individual):
    if not individual.mFitness.isValid():
        individual.mFitness.append(individual.count(True))

lTools.register('evaluate', evalOneMax)
lTools.register('mate', toolbox.twoPointsCx)
lTools.register('mutate', toolbox.flipBitMut, flipIndxPb=0.05)
lTools.register('select', toolbox.tournSel, tournSize=3)

lPop = lTools.population()

CXPB, MUTPB, NGEN = (0.5, 0.2, 40)

# Begin the evolution
for g in range(NGEN):
    print '-- Generation %i --' % g

    lPop[:] = lTools.select(lPop, n=len(lPop))

    # Apply crossover and mutation
    for i in xrange(1, len(lPop), 2):
        if random.random() < CXPB:
            lPop[i - 1], lPop[i] = lTools.mate(lPop[i - 1], lPop[i])
    for i in xrange(len(lPop)):
        if random.random() < MUTPB:
            lPop[i] = lTools.mutate(lPop[i])

    # Evaluate the population
    map(lTools.evaluate, lPop)

    # Gather all the fitnesses in one list and print the stats
    lFitnesses = [lInd.mFitness[0] for lInd in lPop]
    print '  Min %f' % min(lFitnesses)
    print '  Max %f' % max(lFitnesses)
    lSum = float(sum(lFitnesses))
    lSum2 = float(reduce(lambda x, y: x + y*y, lFitnesses, 0))
    lLenght = len(lFitnesses)
    lStdDev = ((lSum2 - (lSum*lSum / lLenght)) / (lLenght - 1))**0.5
    print '  Mean %f' % (lSum/lLenght)
    print '  Std. Dev. %f' % lStdDev

print '-- End of evolution --'