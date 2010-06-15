import sys
import os
import random
import operator
import math
import logging

sys.path.append(os.path.abspath('..'))

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.gp as gp
import eap.algorithms as algorithms

logging.basicConfig(level=logging.DEBUG)

#random.seed(1626)

# Define new functions
def safeDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 0

pset = gp.PrimitiveSet()
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(safeDiv, 2)
pset.addPrimitive(operator.neg, 1)
pset.addPrimitive(math.cos, 1)
pset.addPrimitive(math.sin, 1)
pset.addEphemeralConstant(lambda: random.randint(-1,1))
pset.addTerminal('x')

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("FitnessMax", base.Fitness, weights=(1.0,))

creator.create("Ind_GP", base.Tree, fitness=creator.FitnessMin)
creator.create("Ind_GA", list, fitness=creator.FitnessMax)

tools = toolbox.Toolbox()
tools.register('expr', gp.generate_ramped, pset=pset, min=1, max=2)
tools.register('ind_gp', creator.Ind_GP, content_init=tools.expr)
tools.register('pop_gp', list, content_init=tools.ind_gp, size_init=20)

tools.register('float', random.uniform, -1, 1)
tools.register('ind_ga', creator.Ind_GA, content_init=tools.float, size_init=10)
tools.register('pop_ga', list, content_init=tools.ind_ga, size_init=200)

def refFunc(x):
    return x**4 + x**3 + x**2 + x
    
def evalSymbReg(expr, data):
    # Transform the tree expression in a callable function
    func = tools.lambdify(expr=expr)
    # Evaluate the sum of squared difference between the expression
    # and the real function : x**4 + x**3 + x**2 + x
    values = data
    diff_func = lambda x: (func(x)-refFunc(x))**2
    diff = sum(map(diff_func, values))
    return diff,

tools.register('evaluate', evalSymbReg)

tools.register('select', toolbox.selTournament, tournsize=3)
tools.register('expr_mut', gp.generate_full, pset=pset, min=0, max=2)
tools.register('mate_gp', toolbox.cxTreeUniformOnePoint)
tools.register('mutate_gp', toolbox.mutTreeUniform, expr=tools.expr_mut)
tools.register('lambdify', gp.lambdify, pset=pset, args='x')

tools.register("mate_ga", toolbox.cxTwoPoints)
tools.register("mutate_ga", toolbox.mutGaussian,  mu=0, sigma=0.01, indpb=0.05)

pop_ga = tools.pop_ga()
pop_gp = tools.pop_gp()

best_ga = toolbox.selRandom(pop_ga, 1)[0]
best_gp = toolbox.selRandom(pop_gp, 1)[0]

for ind in pop_gp:
    ind.fitness.values = tools.evaluate(ind, best_ga)  

for ind in pop_ga:
    ind.fitness.values = tools.evaluate(best_gp, ind)

CXPB, MUTPB, NGEN = 0.5, 0.2, 50

# Begin the evolution
for g in range(NGEN):
    print "-- Generation %i --" % g

    pop_ga[:] = tools.select(pop_ga, n=len(pop_ga))
    pop_gp[:] = tools.select(pop_gp, n=len(pop_gp))

    # Apply crossover and mutation
    for i in xrange(1, len(pop_ga), 2):
        if random.random() < CXPB:
            pop_ga[i - 1], pop_ga[i] = tools.mate_ga(pop_ga[i - 1], pop_ga[i])

    for i in xrange(1, len(pop_gp), 2):
        if random.random() < CXPB:
            pop_gp[i - 1], pop_gp[i] = tools.mate_gp(pop_gp[i - 1], pop_gp[i])

    for i in xrange(len(pop_ga)):
        if random.random() < MUTPB:
            pop_ga[i] = tools.mutate_ga(pop_ga[i])

    for i in xrange(len(pop_gp)):
        if random.random() < MUTPB:
            pop_gp[i] = tools.mutate_gp(pop_gp[i])

    # Evaluate the individuals with an invalid fitness     
    for ind in pop_ga:
        if not ind.fitness.valid:
           ind.fitness.values = tools.evaluate(best_gp, ind)
    
    for ind in pop_gp:
        if not ind.fitness.valid:
            ind.fitness.values = tools.evaluate(ind, best_ga)
            
    best_ga = toolbox.selBest(pop_ga, 1)[0]
    best_gp = toolbox.selBest(pop_gp, 1)[0]    

    # Gather all the fitnesses in one list and print the stats
    fits = [ind.fitness.values[0] for ind in pop_ga]
    length = len(pop_ga)
    mean = sum(fits) / length
    sum2 = sum(map(lambda x: x**2, fits))
    std_dev = abs(sum2 / length - mean**2)**0.5
        
    print "--GA Population--"
    print "  Min %f" % min(fits)
    print "  Max %f" % max(fits)
    print "  Avg %f" % (mean)
    print "  Std %f" % std_dev
    
    fits = [ind.fitness.values[0] for ind in pop_gp]    
    print "--GP Population--"
    print "  Min %f" % min(fits)
    print "  Max %f" % max(fits)
    length = len(pop_gp)
    mean = sum(fits) / length
    sum2 = sum(map(lambda x: x**2, fits))
    std_dev = abs(sum2 / length - mean**2)**0.5
    print "  Avg %f" % (mean)
    print "  Std %f" % std_dev

print "Best individual GA is %s, %s" % (best_ga, best_ga.fitness.values)
print "Best individual GP is %s, %s" % (gp.evaluate(best_gp), best_gp.fitness.values)
