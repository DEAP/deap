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

import random
import os
import sys

sys.path.append(os.path.abspath('..'))

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.operators as operators

random.seed(100)

# Instanciate the creator
lCreator = creator.Creator()
# Define a way to build a maximizing fitness
lCreator.define('crtFitness', base.Fitness, weights=(1.0,))
# Define a way to build an individual containing booleans and the previous fitness
lCreator.define('crtIndividual', base.Individual, size=100,
                fitness=lCreator.crtFitness, generator=base.booleanGenerator())
# Define a way to build a population filled with the previous individuals
lCreator.define('crtPopulation', base.Population, size=300,
                generator=lCreator.crtIndividual)

# The function that evauluates an individual and set its fitness
def evalOneMax(individual):
    if not individual.mFitness.isValid():
        individual.mFitness.append(individual.count(True))

# Instanciate a toolbox that will contain the operators
lToolbox = toolbox.Toolbox()
# Add a two points crossover method to the toolbox
lToolbox.register('crossover', operators.twoPointsCx)
# Add a flip bit mutation method to the toolbox with each index having a probability
# of 5% to be flipped
lToolbox.register('mutate', operators.flipBitMut, flipIndxPb=0.05)
# Add a tournament selection method to the toolbox with tournament size of 3
lToolbox.register('select', operators.tournSel, tournSize=3)

# Instanciate the population
lPop = lCreator.crtPopulation()

# Evaluate the population
map(evalOneMax, lPop)

# Each individual has a probability of 50% to be mated (crossover)
CXPB = 0.5
# Each individuals has a probability of 20% to be mutated
MUTPB = 0.2

# Begin the evolution
for g in range(40):
    print 'Generation', g

    # Select then next population
    lPop[:] = lToolbox.select(lPop, n=len(lPop))

    # Build a table of the individuals that should be mated and mutated
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

    # Evaluate the population
    map(evalOneMax, lPop)

    # Gather all the fitnesses in one list and print the stats
    lFitnesses = [lInd.mFitness[0] for lInd in lPop]
    print '\tMinimum :', min(lFitnesses)
    print '\tMaximum :', max(lFitnesses)
    print '\tAverage :', sum(lFitnesses)/len(lFitnesses)

print 'End of evolution'