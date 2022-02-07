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
import matplotlib.pyplot as plt

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMax)

toolbox = base.Toolbox()

GENE_SIZE = 100
ZERO_COUNT = 10

toolbox.register("attr_bool", random.randint, 0, 1)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, GENE_SIZE)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def calc(individual, check):
    diff = 0
    for i in range(len(individual)):
        if individual[i] != check[i]:
            diff += 1
    return diff

CHECK1 = [0] * 0 + [1] * GENE_SIZE
CHECK2 = [0] * ZERO_COUNT + [1] * (GENE_SIZE - ZERO_COUNT)

def evalMoOneMax(individual):
    l = len(individual)
    return l - calc(individual, CHECK1), l - calc(individual, CHECK2)

toolbox.register("evaluate", evalMoOneMax)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.01)

MU = 100
NEIGHBOUR_SIZE = 10
NGEN = 100

CXPB = 0.5
MUTPB = 0.2

stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", numpy.mean, axis=0)
stats.register("std", numpy.std, axis=0)
stats.register("min", numpy.min, axis=0)
stats.register("max", numpy.max, axis=0)

random.seed(64)

pop = toolbox.population(n=MU)
weights = []
for i in range(MU):
    weights.append([i / float(MU - 1), (MU - i - 1) / float(MU - 1)])

EP, logbook = algorithms.moead(pop, toolbox, weights,
                               neighbour_size=NEIGHBOUR_SIZE,
                               scalar_method='tchebycheff',
                               cxpb=CXPB, mutpb=MUTPB, ngen=NGEN,
                               stats=stats, verbose=True)

front = numpy.array([ind.fitness.values for ind in EP])
plt.scatter(front[:,0], front[:,1], c="b")
plt.axis("tight")
plt.show()
