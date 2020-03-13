import array
import random

import numpy

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

npop = 100
neighbour_size = 10
ngen = 100

CXPB = 0.5
MUTPB = 0.2

stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", numpy.mean, axis=0)
stats.register("std", numpy.std, axis=0)
stats.register("min", numpy.min, axis=0)
stats.register("max", numpy.max, axis=0)

random.seed(64)

pop = toolbox.population(n=npop)
weights = []
for i in range(npop):
    weights.append([i / float(npop - 1), (npop - i - 1) / float(npop - 1)])

EP, logbook = algorithms.moead(pop, toolbox, weights,
                               neighbour_size=neighbour_size,
                               scalar_method='tchebycheff',
                               cxpb=CXPB, mutpb=MUTPB, ngen=ngen,
                               stats=stats, verbose=True)

import matplotlib.pyplot as plt

front = numpy.array([ind.fitness.values for ind in EP])
plt.scatter(front[:,0], front[:,1], c="b")
plt.axis("tight")
plt.show()
