## 2.2.1 List of floats
import random
import array
import numpy

from deap import base
from deap import creator
from deap import tools

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

IND_SIZE=10

toolbox = base.Toolbox()
toolbox.register("attr_float", random.random)
toolbox.register("individual", tools.initRepeat, creator.Individual,
                 toolbox.attr_float, n=IND_SIZE)

creator.create("Individual", array.array, typecode="d", fitness=creator.FitnessMax)
creator.create("Individual", numpy.ndarray, fitness=creator.FitnessMax)