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
import eap.evolutiontoolbox as toolbox
import eap.operators as operators
import eap.specialized as specialized
import eap.stats as stats
import random

random.seed(64)

lCreator = creator.Creator()
lCreator.define('crtFitness', base.Fitness, weights=(1.0,))
lCreator.define('crtListIndividual', specialized.BooleanIndividual, size=100,
                fitness=lCreator.crtFitness, generator=base.binaryGenerator())
lCreator.define('crtPopulation', base.ListPopulation, size=300,
                generator=lCreator.crtListIndividual)

def evalOneMax(individual):
    if not individual.mFitness.isValid():
        individual.mFitness.append(individual.count(True))

lToolBox = toolbox.SimpleGAToolBox()
lToolBox.register('mutate', operators.flipBitMut)

lPop = lCreator.crtPopulation()
lPop.suscribe('stats', stats.statistics)

map(evalOneMax, lPop)
lPop.emit()

CXPB = 0.5
MUTPB = 0.2

for g in range(40):
    print 'Generation', g

    lMateIndx = []
    lMutateIndx = []

    for lIndx in xrange(len(lPop)):
        if random.random() < CXPB:
            lMateIndx.append(lIndx)
        if random.random() < MUTPB:
            lMutateIndx.append(lIndx)

    random.shuffle(lMateIndx)
    # Apply crossover on the choosen indexes and replace parents
    for i, j in zip(lMateIndx[::2], lMateIndx[1::2]):
        lPop[i], lPop[j] = lToolBox.mate(lPop[i], lPop[j])
    # Apply mutation on the choosen indexes and replace parents
    for i in lMutateIndx:
        lPop[i] = lToolBox.mutate(lPop[i])

    map(evalOneMax, lPop)

    lPop[:] = lToolBox.select(lPop, n=len(lPop), tournSize=3)
    lPop.emit()

    print '\tMinimum :', stats.getStats('stats')[0]
    print '\tMaximum :', stats.getStats('stats')[1]
    print '\tAverage :', stats.getStats('stats')[2]

print 'End of evolution'
#print lStats.getStats('bestIndividualHistory')
