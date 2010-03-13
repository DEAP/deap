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
import eap.algorithms as algorithms
import eap.toolbox as toolbox
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(1.0,))
lTools.register('individual', base.IndividualES, size=20, esdegree=1, strategy=0.5,
                fitness=lTools.fitness, generator=base.realGenerator(0.0, 1.0))
lTools.register('population', base.Population, size=50,
                generator=lTools.individual)

def evalOneMax(individual):
    if not individual.mFitness.isValid():
        individual.mFitness.append(sum(individual))

def blendES(indOne, indTwo, alpha):
    lChild1, lChild2 = toolbox.blendESCx(indOne, indTwo, alpha)
    for i in xrange(len(lChild1)):
        if lChild1[i] > 1.0 or lChild1[i] < 0.0:
            lChild1[i] = lChild1[i] % 1.0
        if lChild2[i] > 1.0 or lChild2[i] < 0.0:
            lChild2[i] = lChild2[i] % 1.0
    return lChild1, lChild2

def gaussMut(individual, mutIndxPb):
    lMutant = toolbox.gaussESMut(individual, mutIndxPb)
    for i in xrange(len(lMutant)):
        if lMutant[i] > 1.0 or lMutant[i] < 0.0:
            lMutant[i] = lMutant[i] % 1.0
    return lMutant


lTools.register('evaluate', evalOneMax)
lTools.register('mate', blendES, alpha=0.5)
lTools.register('mutate', gaussMut, mutIndxPb=0.05)
lTools.register('select', toolbox.tournSel, tournSize=2)

lPop = lTools.population()
algorithms.mupluslambdaEA(lTools, lPop, 1, 100)

print toolbox.bestSel(lPop, n=1)