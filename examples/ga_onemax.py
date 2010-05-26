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

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
creator.create("Population", list)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_bool", random.randint, 0, 1)

# Structure initializers
tools.regInit("individual", creator.Individual, content=tools.attr_bool, size=100)
tools.regInit("population", creator.Population, content=tools.individual, size=300)

def evalOneMax(individual):
    return sum(individual),

tools.register("evaluate", evalOneMax)
tools.register("mate", toolbox.cxTwoPoints)
tools.register("mutate", toolbox.mutFlipBit, indpb=0.05)
tools.register("select", toolbox.selTournament, tournsize=3)

pop = tools.population()
CXPB, MUTPB, NGEN = 0.5, 0.2, 40

# Evaluate the entire population
for ind in pop:
    ind.fitness.values = tools.evaluate(ind)

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
            ind.fitness.values = tools.evaluate(ind)

    # Gather all the fitnesses in one list and print the stats
    fits = [ind.fitness.values[0] for ind in pop]
    print "  Min %f" % min(fits)
    print "  Max %f" % max(fits)
    lenght = len(pop)
    mean = sum(fits) / lenght
    sum2 = sum(map(lambda x: x**2, fits))
    std_dev = abs(sum2 / lenght - mean**2)**0.5
    print "  Mean %f" % (mean)
    print "  Std. Dev. %f" % std_dev

print "-- End of (successful) evolution --"

best_ind = toolbox.selBest(pop, 1)[0]
print "Best individual is %r, %r" % (best_ind, best_ind.fitness.values)
