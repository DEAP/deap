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
import random


sys.path.append("..")


import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox


random.seed(64)

creator.create("FitnessMax", (base.Fitness,), {"weights" : (1.0,)})
creator.create("Individual", (base.Array,), {"fitness" : creator.FitnessMax})
creator.create("Population", (base.List,))

tools = toolbox.Toolbox()
tools.register("individual", creator.Individual, size=100, typecode="b",
		content=lambda: random.randint(0, 1))
tools.register("population", creator.Population, size=300,
		content=tools.individual)

def evalOneMax(individual):
    return [sum(individual)]

tools.register("evaluate", evalOneMax)
tools.register("mate", toolbox.twoPointsCx)
tools.register("mutate", toolbox.flipBitMut, indpb=0.05)
tools.register("select", toolbox.tournSel, tournsize=3)

pop = tools.population()
CXPB, MUTPB, NGEN = 0.5, 0.2, 40

# Evaluate the entire population
for ind in pop:
    ind.fitness.extend(tools.evaluate(ind))

# Begin the evolution
for g in range(NGEN):
    print "-- Generation %i --" % g

    pop[:] = tools.select(pop, n=len(pop))

    # Apply crossover and mutation
    for i in xrange(1, len(pop), 2):
        if random.random() < CXPB:
            pop[i - 1], pop[i] = tools.mate(pop[i - 1], pop[i])

    for i in xrange(len(pop)):
        if random.random() < MUTPB:
            pop[i] = tools.mutate(pop[i])

    # Evaluate the individuals with an invalid fitness
    for ind in pop:
        if not ind.fitness.valid:
            ind.fitness.extend(tools.evaluate(ind))

    # Gather all the fitnesses in one list and print the stats
    fits = [ind.fitness[0] for ind in pop]
    print "  Min %f" % min(fits)
    print "  Max %f" % max(fits)
    lenght = len(pop)
    mean = sum(fits) / lenght
    sum2 = sum(map(lambda x: x**2, fits))
    std_dev = (sum2 / lenght - mean**2)**0.5
    print "  Mean %f" % (mean)
    print "  Std. Dev. %f" % std_dev

print "-- End of (successful) evolution --"

best_ind = toolbox.bestSel(pop, 1)[0]
print "Best individual: %s" % str(best_ind)
print "Best individual's fitness: %s" % str(best_ind.fitness)
