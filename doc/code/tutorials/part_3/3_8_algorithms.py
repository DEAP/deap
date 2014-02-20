## 3.7 Variations
import random

from deap import base
from deap import creator
from deap import tools

## Data structure and initializer creation

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("attr_float", random.random)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, 10)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def onemax(individual):
    return sum(individual),

toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", onemax)

pop = toolbox.population(n=100)
CXPB, MUTPB, NGEN= 0.7, 0.3, 25

fitnesses = toolbox.map(toolbox.evaluate, pop)
for ind, fit in zip(pop, fitnesses):
    ind.fitness.values = fit

from deap import algorithms

algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=50)
