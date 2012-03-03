## 2.3.2 Grid
import random

from deap import base
from deap import creator
from deap import tools

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

IND_SIZE = 20

toolbox = base.Toolbox()
toolbox.register("attr_float", random.random)
toolbox.register("individual", tools.initRepeat, creator.Individual,
                 toolbox.attr_float, n=IND_SIZE)

N_ROW, N_COL = 20, 10

toolbox.register("row", tools.initRepeat, list, toolbox.individual, n=N_COL)
toolbox.register("population", tools.initRepeat, list, toolbox.row, n=N_ROW)

population = toolbox.population()
population[9][9]
