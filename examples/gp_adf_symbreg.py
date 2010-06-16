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

import sys
import os
import random
import operator
import math
import logging
import copy
import inspect

sys.path.append(os.path.abspath('..'))

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.gp as gp

logging.basicConfig(level=logging.DEBUG)

#random.seed(1626)

# Define new functions
def safeDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 0


adfset = gp.PrimitiveSet()
adfset.addPrimitive(operator.add, 2)
adfset.addPrimitive(operator.sub, 2)
adfset.addPrimitive(operator.mul, 2)
adfset.addPrimitive(safeDiv, 2)
adfset.addPrimitive(operator.neg, 1)
adfset.addPrimitive(math.cos, 1)
adfset.addPrimitive(math.sin, 1)
adfset.addADF("ADF1", 2)
adfset.addADF("ADF2", 2)
adfset.addTerminal("ARG0")
adfset.addTerminal("ARG1")

adfset2 = gp.PrimitiveSet()
adfset2.addPrimitive(operator.add, 2)
adfset2.addPrimitive(operator.sub, 2)
adfset2.addPrimitive(operator.mul, 2)
adfset2.addPrimitive(safeDiv, 2)
adfset2.addPrimitive(operator.neg, 1)
adfset2.addPrimitive(math.cos, 1)
adfset2.addPrimitive(math.sin, 1)
adfset2.addADF("ADF2", 2)
adfset2.addTerminal("ARG0")
adfset2.addTerminal("ARG1")

adfset3 = gp.PrimitiveSet()
adfset3.addPrimitive(operator.add, 2)
adfset3.addPrimitive(operator.sub, 2)
adfset3.addPrimitive(operator.mul, 2)
adfset3.addPrimitive(safeDiv, 2)
adfset3.addPrimitive(operator.neg, 1)
adfset3.addPrimitive(math.cos, 1)
adfset3.addPrimitive(math.sin, 1)
adfset3.addTerminal("ARG0")
adfset3.addTerminal("ARG1")

pset = gp.PrimitiveSet()
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(safeDiv, 2)
pset.addPrimitive(operator.neg, 1)
pset.addPrimitive(math.cos, 1)
pset.addPrimitive(math.sin, 1)
pset.addEphemeralConstant(lambda: random.randint(-1,1))
pset.addADF("ADF0", 2)
pset.addADF("ADF1", 2)
pset.addADF("ADF2", 2)
pset.addTerminal('x')

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

tools = toolbox.Toolbox()
tools.register('adf_expr', gp.generate_full, pset=adfset, min=1, max=2)
tools.register('adf_expr2', gp.generate_full, pset=adfset2, min=1, max=2)
tools.register('adf_expr3', gp.generate_full, pset=adfset3, min=1, max=2)
tools.register('fun_expr', gp.generate_ramped, pset=pset, min=1, max=2)

tools.register('ADF0', base.Tree, content_init=tools.adf_expr)
tools.register('ADF1', base.Tree, content_init=tools.adf_expr2)
tools.register('ADF2', base.Tree, content_init=tools.adf_expr3)

tools.register('FUN', base.Tree, content_init=tools.fun_expr)

tools.register('individual', creator.Individual, 
                             content_init=[tools.FUN, tools.ADF0, tools.ADF1, tools.ADF2], 
                             size_init=4)
tools.register('population', list, content_init=tools.individual, size_init=100)

def evalSymbReg(individual):
    # Transform the tree expression in a callable function
    func = tools.lambdify(expr=individual)
    # Evaluate the sum of squared difference between the expression
    # and the real function : x**4 + x**3 + x**2 + x
    values = (x/10. for x in xrange(-10,10))
    diff_func = lambda x: (func(x)-(x**4 + x**3 + x**2 + x))**2
    diff = sum(map(diff_func, values))
    return diff,

tools.register('evaluate', evalSymbReg)
tools.register('select', toolbox.selTournament, tournsize=3)
tools.register('mate', toolbox.cxTreeUniformOnePoint)
tools.register('fun_mut', gp.generate_full, pset=pset, min=0, max=2)
tools.register('mutate_fun', toolbox.mutTreeUniform, expr=tools.fun_mut)
tools.register('adf_mut', gp.generate_full, pset=adfset, min=1, max=2)
tools.register('mutate_adf', toolbox.mutTreeUniform, expr=tools.adf_mut)
tools.register('adf_mut2', gp.generate_full, pset=adfset2, min=1, max=2)
tools.register('mutate_adf2', toolbox.mutTreeUniform, expr=tools.adf_mut2)
tools.register('adf_mut3', gp.generate_full, pset=adfset3, min=1, max=2)
tools.register('mutate_adf3', toolbox.mutTreeUniform, expr=tools.adf_mut2)
tools.register('lambdify', gp.lambdifyList, pset=[pset, adfset, adfset2, adfset3], args='x')

pop = tools.population()

CXPB, MUTPB, NGEN = 0.5, 0.2, 10

# Evaluate the entire population
for ind in pop:
    ind.fitness.values = tools.evaluate(ind)

for g in range(NGEN):
    print "-- Generation %i --" % g

    pop = tools.select(pop, n=len(pop))

    # Apply crossover and mutation
    for i in xrange(1, len(pop), 2):
        pop[i] = copy.deepcopy(pop[i])
        pop[i-1] = copy.deepcopy(pop[i-1])
        for j in xrange(0, len(pop[i])):
            if random.random() < CXPB:
                pop[i - 1][j], pop[i][j] = tools.mate(pop[i - 1][j], pop[i][j])
        del pop[i].fitness.values
        del pop[i-1].fitness.values

    for i in xrange(len(pop)):
        if random.random() < MUTPB:
            pop[i] = copy.deepcopy(pop[i])
            pop[i][0] = tools.mutate_fun(pop[i][0])
            del pop[i].fitness.values

    for i in xrange(len(pop)):
        if random.random() < MUTPB:
            pop[i] = copy.deepcopy(pop[i])
            pop[i][1] = tools.mutate_adf(pop[i][1])
            del pop[i].fitness.values
                
    for i in xrange(len(pop)):
        if random.random() < MUTPB:
            pop[i] = copy.deepcopy(pop[i])
            pop[i][2] = tools.mutate_adf2(pop[i][2])
            del pop[i].fitness.values  
            
    for i in xrange(len(pop)):
        if random.random() < MUTPB:
            pop[i] = copy.deepcopy(pop[i])
            pop[i][3] = tools.mutate_adf2(pop[i][3])
            del pop[i].fitness.values               
                
    # Evaluate the individuals with an invalid fitness
    for ind in pop:
        if not ind.fitness.valid:
            ind.fitness.values = tools.evaluate(ind)

    # Gather all the fitnesses in one list and print the stats
    fits = [ind.fitness.values[0] for ind in pop]
    print "  Min %f" % min(fits)
    print "  Max %f" % max(fits)
    lenght = len(pop)
    mean = sum(fits) / lenght
    sum2 = sum(map(lambda x: x**2, fits))
    std_dev = (sum2 / lenght - mean**2)
    print "  Avg %f" % (mean)
    print "  Std %f" % std_dev

best = toolbox.selBest(pop,1)[0]

print 'Best individual : ', gp.evaluate(best[0]), best.fitness


