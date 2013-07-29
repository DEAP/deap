#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.
"""This example shows a possible answer to a problem that can be found in this
xkcd comics: http://xkcd.com/287/. In the comic, the characters want to get
exactly 15.05$ worth of appetizers, as fast as possible."""
import random

from collections import Counter

# We delete the reduction function of the Counter because it doesn't copy added
# attributes. Because we create a class that inherit from the Counter, the
# fitness attribute was not copied by the deepcopy.
del Counter.__reduce__

import numpy

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

IND_INIT_SIZE = 3

# Create the item dictionary: item id is an integer, and value is 
# a (name, weight, value) 3-uple. Since the comic didn't specified a time for
# each menu item, random was called to generate a time.

item_names = ["Mixed Fruit", "French Fries", "Side Salad", "Hot Wings",
             "Mozzarella Sticks", "Sampler Plate"]

item_values = [2.15, 2.75, 3.35, 3.55, 4.2, 5.8]

items = dict((name, (price, random.uniform(1, 5))) for name, price in zip(item_names, item_values))


creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", Counter, fitness=creator.Fitness)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_item", random.choice, item_names)

# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, 
    toolbox.attr_item, IND_INIT_SIZE)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evalXkcd(individual, target_price):
    """Evaluates the fitness and return the error on the price and the time
    taken by the order."""
    price = 0.0
    time = 0.0
    for item in individual:
        price += items[item][0]
        time += items[item][1]
    return abs(price - target_price), time

def mateCounter(ind1, ind2, indpb = 0.1):
    """Swaps the number of perticular items between two individuals"""
    for key in items:
        if random.random() < indpb:
            ind1[key], ind2[key] = ind2[key], ind1[key]
    return ind1, ind2

def mutateCounter(individual):
    """Adds or remove an item from an individual"""
    if random.randint(0,1) > 0:
        individual.update([random.choice(item_names)])
    else:
        val = random.choice(item_names)
        individual.subtract([val])
        if individual[val] < 0:
            del individual[val]
    return individual,

toolbox.register("evaluate", evalXkcd, target_price = 15.05)
toolbox.register("mate", mateCounter)
toolbox.register("mutate", mutateCounter)
toolbox.register("select", tools.selNSGA2)

def main():
    NGEN = 40 
    MU = 100
    LAMBDA = 200
    CXPB = 0.3
    MUTPB = 0.6

    pop = toolbox.population(n=MU)
    hof = tools.ParetoFront()
    stats1 = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats1.register("avg", numpy.mean)
    stats1.register("std", numpy.std)
    stats1.register("min", numpy.min)
    stats2 = tools.Statistics(lambda ind: ind.fitness.values[1])
    stats2.register("avg", numpy.mean)
    stats2.register("std", numpy.std)
    stats2.register("min", numpy.min)
    stats = tools.MultiStatistics(price=stats1, time=stats2)

    algorithms.eaMuPlusLambda(pop, toolbox, MU, LAMBDA, CXPB, MUTPB, NGEN,
                              stats, halloffame=hof)

    return pop, stats, hof

if __name__ == "__main__":
    _, _, hof = main()
    from matplotlib import pyplot as plt
    error_price = [i.fitness.values[0] for i in hof]
    time = [i.fitness.values[1] for i in hof]
    plt.plot(error_price, time, 'bo')
    plt.xlabel("Error on the price")
    plt.ylabel("Total time")
    plt.show()
