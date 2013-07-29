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
from operator import attrgetter
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
ITEMS_NAME = "Mixed Fruit", "French Fries", "Side Salad", "Hot Wings", "Mozzarella Sticks", "Sampler Plate"
ITEMS_PRICE = 2.15, 2.75, 3.35, 3.55, 4.2, 5.8
ITEMS = dict((name, (price, random.uniform(1, 5))) for name, price in zip(ITEMS_NAME, ITEMS_PRICE))

creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", Counter, fitness=creator.Fitness)

toolbox = base.Toolbox()
toolbox.register("attr_item", random.choice, ITEMS_NAME)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_item, IND_INIT_SIZE)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evalXKCD(individual, target_price):
    """Evaluates the fitness and return the error on the price and the time
    taken by the order if the chef can cook everything in parallel."""
    price = 0.0
    times = list()
    for item, number in individual.items():
        price += ITEMS[item][0] * number
        times.append(ITEMS[item][1])
    return abs(price - target_price), max(times)

def cxCounter(ind1, ind2, indpb):
    """Swaps the number of perticular items between two individuals"""
    for key in ITEMS.keys():
        if random.random() < indpb:
            ind1[key], ind2[key] = ind2[key], ind1[key]
    return ind1, ind2

def mutCounter(individual):
    """Adds or remove an item from an individual"""
    if random.random() > 0.5:
        individual.update([random.choice(ITEMS_NAME)])
    else:
        val = random.choice(ITEMS_NAME)
        individual.subtract([val])
        if individual[val] < 0:
            del individual[val]
    return individual,

toolbox.register("evaluate", evalXKCD, target_price=15.05)
toolbox.register("mate", cxCounter, indpb=0.5)
toolbox.register("mutate", mutCounter)
toolbox.register("select", tools.selNSGA2)

def main():
    NGEN = 40
    MU = 100
    LAMBDA = 200
    CXPB = 0.3
    MUTPB = 0.6

    pop = toolbox.population(n=MU)
    hof = tools.ParetoFront()
    
    price_stats = tools.Statistics(key=lambda ind: ind.fitness.values[0])
    time_stats = tools.Statistics(key=lambda ind: ind.fitness.values[1])
    stats = tools.MultiStatistics(price=price_stats, time=time_stats)
    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)

    algorithms.eaMuPlusLambda(pop, toolbox, MU, LAMBDA, CXPB, MUTPB, NGEN,
                              stats, halloffame=hof)

    return pop, stats, hof

if __name__ == "__main__":
    _, _, hof = main()
    from matplotlib import pyplot as plt
    error_price = [i.fitness.values[0] for i in hof]
    time = [i.fitness.values[1] for i in hof]
    plt.plot(error_price, time, 'bo')
    plt.xlabel("Price difference")
    plt.ylabel("Total time")
    plt.show()
