## 3.1 A First Individual
import random

from deap import base
from deap import creator
from deap import tools

IND_SIZE = 5

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("attr_float", random.random)
toolbox.register("individual", tools.initRepeat, creator.Individual,
                 toolbox.attr_float, n=IND_SIZE)

ind1 = toolbox.individual()

print ind1               # [0.86..., 0.27..., 0.70..., 0.03..., 0.87...]
print ind1.fitness.valid # False

## 3.2 Evaluation
def evaluate(individual):
    # Do some hard computing on the individual
    a = sum(individual)
    b = len(individual)
    return a, 1. / b

ind1.fitness.values = evaluate(ind1)
print ind1.fitness.valid    # True
print ind1.fitness          # (2.73, 0.2)

## 3.3 Mutation
mutant = toolbox.clone(ind1)
ind2, = tools.mutGaussian(mutant, mu=0.0, sigma=0.2, indpb=0.2)
del mutant.fitness.values

print ind2 is mutant    # True
print mutant is ind1    # False

## 3.4 Crossover
child1, child2 = [toolbox.clone(ind) for ind in (ind1, ind2)]
tools.cxBlend(child1, child2, 0.5)
del child1.fitness.values
del child2.fitness.values

## 3.5 Selection
selected = tools.selBest([child1, child2], 2)
print child1 in selected	# True

## 3.5 Note
LAMBDA = 10
toolbox.register("select", tools.selRandom)
population = [ind1, ind2]*10
selected = toolbox.select(population, LAMBDA)
offspring = [toolbox.clone(ind) for ind in selected]
