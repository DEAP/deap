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

import random
import operator
import math

import numpy

from deap import base
from deap import creator
from deap import gp
from deap import tools

# Define new functions
def protectedDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 1

adfset2 = gp.PrimitiveSet("ADF2", 2)
adfset2.addPrimitive(operator.add, 2)
adfset2.addPrimitive(operator.sub, 2)
adfset2.addPrimitive(operator.mul, 2)
adfset2.addPrimitive(protectedDiv, 2)
adfset2.addPrimitive(operator.neg, 1)
adfset2.addPrimitive(math.cos, 1)
adfset2.addPrimitive(math.sin, 1)

adfset1 = gp.PrimitiveSet("ADF1", 2)
adfset1.addPrimitive(operator.add, 2)
adfset1.addPrimitive(operator.sub, 2)
adfset1.addPrimitive(operator.mul, 2)
adfset1.addPrimitive(protectedDiv, 2)
adfset1.addPrimitive(operator.neg, 1)
adfset1.addPrimitive(math.cos, 1)
adfset1.addPrimitive(math.sin, 1)
adfset1.addADF(adfset2)

adfset0 = gp.PrimitiveSet("ADF0", 2)
adfset0.addPrimitive(operator.add, 2)
adfset0.addPrimitive(operator.sub, 2)
adfset0.addPrimitive(operator.mul, 2)
adfset0.addPrimitive(protectedDiv, 2)
adfset0.addPrimitive(operator.neg, 1)
adfset0.addPrimitive(math.cos, 1)
adfset0.addPrimitive(math.sin, 1)
adfset0.addADF(adfset1)
adfset0.addADF(adfset2)

pset = gp.PrimitiveSet("MAIN", 1)
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(protectedDiv, 2)
pset.addPrimitive(operator.neg, 1)
pset.addPrimitive(math.cos, 1)
pset.addPrimitive(math.sin, 1)
pset.addEphemeralConstant("rand101", lambda: random.randint(-1, 1))
pset.addADF(adfset0)
pset.addADF(adfset1)
pset.addADF(adfset2)
pset.renameArguments(ARG0='x')

psets = (pset, adfset0, adfset1, adfset2)

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Tree", gp.PrimitiveTree)

creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register('adf_expr0', gp.genFull, pset=adfset0, min_=1, max_=2)
toolbox.register('adf_expr1', gp.genFull, pset=adfset1, min_=1, max_=2)
toolbox.register('adf_expr2', gp.genFull, pset=adfset2, min_=1, max_=2)
toolbox.register('main_expr', gp.genHalfAndHalf, pset=pset, min_=1, max_=2)

toolbox.register('ADF0', tools.initIterate, creator.Tree, toolbox.adf_expr0)
toolbox.register('ADF1', tools.initIterate, creator.Tree, toolbox.adf_expr1)
toolbox.register('ADF2', tools.initIterate, creator.Tree, toolbox.adf_expr2)
toolbox.register('MAIN', tools.initIterate, creator.Tree, toolbox.main_expr)

func_cycle = [toolbox.MAIN, toolbox.ADF0, toolbox.ADF1, toolbox.ADF2]

toolbox.register('individual', tools.initCycle, creator.Individual, func_cycle)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)

def evalSymbReg(individual):
    # Transform the tree expression in a callable function
    func = toolbox.compile(individual)
    # Evaluate the sum of squared difference between the expression
    # and the real function : x**4 + x**3 + x**2 + x
    values = (x/10. for x in range(-10, 10))
    diff_func = lambda x: (func(x)-(x**4 + x**3 + x**2 + x))**2
    diff = sum(map(diff_func, values))
    return diff,

toolbox.register('compile', gp.compileADF, psets=psets)
toolbox.register('evaluate', evalSymbReg)
toolbox.register('select', tools.selTournament, tournsize=3)
toolbox.register('mate', gp.cxOnePoint)
toolbox.register('expr', gp.genFull, min_=1, max_=2)
toolbox.register('mutate', gp.mutUniform, expr=toolbox.expr)

def main():
    random.seed(1024)
    ind = toolbox.individual()
    
    pop = toolbox.population(n=100)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"
    
    CXPB, MUTPB, NGEN = 0.5, 0.2, 40
    
    # Evaluate the entire population
    for ind in pop:
        ind.fitness.values = toolbox.evaluate(ind)

    hof.update(pop)
    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(pop), **record)
    print(logbook.stream)
    
    for g in range(1, NGEN):
        # Select the offspring
        offspring = toolbox.select(pop, len(pop))
        # Clone the offspring
        offspring = [toolbox.clone(ind) for ind in offspring]
    
        # Apply crossover and mutation
        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            for tree1, tree2 in zip(ind1, ind2):
                if random.random() < CXPB:
                    toolbox.mate(tree1, tree2)
                    del ind1.fitness.values
                    del ind2.fitness.values

        for ind in offspring:
            for tree, pset in zip(ind, psets):
                if random.random() < MUTPB:
                    toolbox.mutate(individual=tree, pset=pset)
                    del ind.fitness.values
                            
        # Evaluate the individuals with an invalid fitness
        invalids = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalids:
            ind.fitness.values = toolbox.evaluate(ind)
                
        # Replacement of the population by the offspring
        pop = offspring
        hof.update(pop)
        record = stats.compile(pop)
        logbook.record(gen=g, evals=len(invalids), **record)
        print(logbook.stream)
    
    print('Best individual : ', hof[0][0], hof[0].fitness)
    
    return pop, stats, hof
    
if __name__ == "__main__":
    main()

