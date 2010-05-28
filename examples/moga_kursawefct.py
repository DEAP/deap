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

import array
import logging
import math
import sys
import random
from itertools import imap
from operator import sub

sys.path.append("..")
logging.basicConfig(level=logging.INFO)

import eap.algorithms as algorithms
import eap.base as base
import eap.creator as creator
import eap.halloffame as halloffame
import eap.toolbox as toolbox

random.seed(64)

creator.create("FitnessMax", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", array.array, fitness=creator.FitnessMax)
creator.create("Population", list)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_float", random.uniform, -5, 5)

# Structure initializers
tools.regInit("individual", creator.Individual, content=tools.attr_float, size=3, args=("f",))
tools.regInit("population", creator.Population, content=tools.individual, size=50)

def evalKursawe(ind):
    f1 = sum(map(lambda x, y: -10 * math.exp(-0.2 * math.sqrt(x * x + y * y)), ind[:-1], ind[1:]))
    f2 = sum(map(lambda x: abs(x)**0.8 + 5 * math.sin(x * x * x), ind[:]))
    return f1, f2

def mate(ind1, ind2, *args, **kargs):
    child1, child2 = toolbox.cxBlend(ind1, ind2, *args, **kargs)
    for i in xrange(len(child1)):
        if child1[i] > 5:
            child1[i] = 5
        elif child1[i] < -5:
            child1[i] = -5
        if child2[i] > 5:
            child2[i] = 5
        elif child2[i] < -5:
            child2[i] = -5
    
    return child1, child2

def mutate(ind, *args, **kargs):
    mutant = toolbox.mutGaussian(ind, *args, **kargs)
    for i in xrange(len(mutant)):
        if mutant[i] > 5:
            mutant[i] = 5
        elif mutant[i] < -5:
            mutant[i] = -5
    return mutant

tools.register("evaluate", evalKursawe)
tools.register("mate", mate, alpha=1.5)
tools.register("mutate", mutate, sigma=3, indpb=0.3)
tools.register("select", toolbox.nsga2)

pop = tools.population()
hof = halloffame.ParetoFront()

algorithms.eaMuPlusLambda(tools, pop, 50, 100, cxpb=0.5, mutpb=0.2, ngen=50, halloffame=hof)

logging.info("Best individual for measure 1 is %r, %r", hof[0], hof[0].fitness.values)
logging.info("Best individual for measure 2 is %r, %r", hof[-1], hof[-1].fitness.values)

# You can plot the Hall of Fame if you have matplotlib installed
#import matplotlib.pyplot as plt
#plt.figure()
#fit1 = [ind.fitness.values[0] for ind in hof]
#fit2 = [ind.fitness.values[1] for ind in hof]
#plt.scatter(fit1, fit2)
#plt.show()
