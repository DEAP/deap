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


import random
import array

import numpy

from itertools import chain

from deap import base
from deap import benchmarks
from deap import creator
from deap import tools

# Problem dimension
NDIM = 10

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

def mutDE(y, a, b, c, f):
    size = len(y)
    for i in range(len(y)):
        y[i] = a[i] + f*(b[i]-c[i])
    return y

def cxBinomial(x, y, cr):
    size = len(x)
    index = random.randrange(size)
    for i in range(size):
        if i == index or random.random() < cr:
            x[i] = y[i]
    return x

def cxExponential(x, y, cr):
    size = len(x)
    index = random.randrange(size)
    # Loop on the indices index -> end, then on 0 -> index
    for i in chain(range(index, size), range(0, index)):
        x[i] = y[i]
        if random.random() < cr:
            break
    return x

toolbox = base.Toolbox()
toolbox.register("attr_float", random.uniform, -3, 3)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, NDIM)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("mutate", mutDE, f=0.8)
toolbox.register("mate", cxExponential, cr=0.8)
toolbox.register("select", tools.selRandom, k=3)
toolbox.register("evaluate", benchmarks.griewank)

def main():
    # Differential evolution parameters
    MU = NDIM * 10
    NGEN = 200    
    
    pop = toolbox.population(n=MU);
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"
    
    # Evaluate the individuals
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(pop), **record)
    print(logbook.stream)

    for g in range(1, NGEN):
        children = []
        for agent in pop:
            # We must clone everything to ensure independance
            a, b, c = [toolbox.clone(ind) for ind in toolbox.select(pop)]
            x = toolbox.clone(agent)
            y = toolbox.clone(agent)
            y = toolbox.mutate(y, a, b, c)
            z = toolbox.mate(x, y)
            del z.fitness.values
            children.append(z)
            
        fitnesses = toolbox.map(toolbox.evaluate, children)
        for (i, ind), fit in zip(enumerate(children), fitnesses):
            ind.fitness.values = fit
            if ind.fitness > pop[i].fitness:
                pop[i] = ind
        
        hof.update(pop)
        record = stats.compile(pop)
        logbook.record(gen=g, evals=len(pop), **record)
        print(logbook.stream)
    
    print("Best individual is ", hof[0])
    print("with fitness", hof[0].fitness.values[0])
    return logbook
            
if __name__ == "__main__":
    main()
