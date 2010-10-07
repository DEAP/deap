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

import copy
import sys
import random
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from eap import algorithms
from eap import base
from eap import creator
from eap import halloffame
from eap import toolbox

MAX_ITEM = 50
MAX_WEIGHT = 50

creator.create("Fitness", base.Fitness, weights=(-1.0, 1.0))
creator.create("Individual", set, fitness=creator.Fitness)
creator.create("Population", list)

# Create the item dictionary, items' name is an integer, and value is a (weight, value) 2-uple
items = dict([(i, (random.randint(1, 10), random.uniform(0, 100))) for i in xrange(100)])

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_item", random.choice, items.keys())

# Structure initializers
tools.register("individual", creator.Individual, content_init=tools.attr_item, size_init=30)
tools.register("population", creator.Population, content_init=tools.individual, size_init=100)

def evalKnapsack(individual):
    weight = 0.0
    value = 0.0
    for item in individual:
        weight += items[item][0]
        value += items[item][1]
    if len(individual) > MAX_ITEM or weight > MAX_WEIGHT:
        return 10000, 0             # Ensure overweighted bags are dominated
    return weight, value

def cxSet(ind1, ind2):
    """Apply a crossover operation on input sets. The first child is the
    intersection of the two sets, the second child is the difference of the
    two sets.
    """
    temp = set(ind1)                # Used in order to keep type
    ind1 &= ind2                    # Intersection (inplace)
    ind2 ^= temp                    # Symmetric Difference (inplace)
    
def mutSet(individual):
    """Mutation that pops or add an element."""
    if random.random() < 0.5:
        if len(individual) > 0:     # We cannot pop from an empty set
            individual.pop()
    else:
        individual.add(random.choice(items.keys()))

tools.register("evaluate", evalKnapsack)
tools.register("mate", cxSet)
tools.register("mutate", mutSet)
tools.register("select", toolbox.spea2)

if __name__ == "__main__":
    random.seed(64)         # Seed does not include item creation

    pop = tools.population()
    hof = halloffame.ParetoFront()
    
    algorithms.eaMuPlusLambda(tools, pop, 50, 100, 0.7, 0.2, 50, hof)
    
    logging.info("Best individual for measure 1 is %s, %s", 
                 hof[0], hof[0].fitness.values)
    logging.info("Best individual for measure 2 is %s, %s", 
                 hof[-1], hof[-1].fitness.values)

    # # You can plot the Hall of Fame if you have matplotlib installed
    # import matplotlib.pyplot as plt
    # plt.figure()
    # weights = [ind.fitness.values[0] for ind in hof]
    # values = [ind.fitness.values[1] for ind in hof]
    # plt.scatter(weights, values)
    # plt.xlabel("Weight")
    # plt.ylabel("Value")
    # plt.show()
