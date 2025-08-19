#!/usr/bin/env python3
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

import array
import random

import numpy

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from functools import partial

maxval = [4, 100, 100, 1, 10000]

creator.create("FitnessMax", base.Fitness, weights=(1.0,))

creator.create(
    "Individual",
    list,
    fitness=creator.FitnessMax
)

toolbox = base.Toolbox()


# Custom Attribute generator
def random_max(maxval):
    from random import randint
    '''
    Return Random list with various max but fixed integer at the begging
    '''
    olist = []
    olist.append(1)
    olist.append(3)
    olist.append(2)
    for i, val in enumerate(maxval):
        olist.append(randint(0, val))
    return olist


# Structure initializers
toolbox.register(
    "individual",
    tools.initIterate,
    creator.Individual,
    partial(random_max, maxval),
)

toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def evalOneMax(individual):
    return sum(individual),


toolbox.register("evaluate", evalOneMax)

toolbox.register("mate", tools.cxTwoPoint)

toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)


def main():
    random.seed(64)

    pop = toolbox.population(n=2000)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    pop, log = algorithms.eaSimple(
        pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=200,
        stats=stats, halloffame=hof, verbose=True
    )

    return pop, log, hof


if __name__ == "__main__":
    pop, log, hof = main()
    print("best individual", hof[0])
    print("maxval         ", maxval)
