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

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

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
algorithms.simpleEA(lTools, lPop, 0.5, 0.2, 50)

