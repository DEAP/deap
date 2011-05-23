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

import array
import logging
import math
import sys
import random

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from deap import algorithms
from deap import base
from deap import creator
from deap import operators
from deap import toolbox

creator.create("FitnessMax", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", array.array, typecode='f', fitness=creator.FitnessMax)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_float", random.uniform, -5, 5)

# Structure initializers
tools.register("individual", creator.Individual, toolbox.Repeat(tools.attr_float, 3))
tools.register("population", list, toolbox.Repeat(tools.individual, 50))

def evalKursawe(ind):
    f1 = sum(-10 * math.exp(-0.2 * math.sqrt(x * x + y * y)) for x, y in zip(ind[:-1], ind[1:]))
    f2 = sum(abs(x)**0.8 + 5 * math.sin(x * x * x) for x in ind)
    return f1, f2

def checkBounds(min, max):
    def decCheckBounds(func):
        def wrapCheckBounds(*args, **kargs):
            offsprings = func(*args, **kargs)
            for child in offsprings:
                for i in xrange(len(child)):
                    if child[i] > max:
                        child[i] = max
                    elif child[i] < min:
                        child[i] = min
            return offsprings
        return wrapCheckBounds
    return decCheckBounds

tools.register("evaluate", evalKursawe)
tools.register("mate", operators.cxBlend, alpha=1.5)
tools.register("mutate", operators.mutGaussian, mu=0, sigma=3, indpb=0.3)
tools.register("select", operators.selNSGA2)

tools.decorate("mate", checkBounds(-5, 5))
tools.decorate("mutate", checkBounds(-5, 5)) 

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    random.seed(64)

    pop = tools.population()
    hof = operators.ParetoFront()
    stats = tools.clone(stats_t)
    
    algorithms.eaMuPlusLambda(tools, pop, mu=50, lambda_=100, 
                              cxpb=0.5, mutpb=0.2, ngen=50, 
                              stats=stats, halloffame=hof)
    
    logging.info("Best individual for measure 1 is %s, %s", 
                 hof[0], hof[0].fitness.values)
    logging.info("Best individual for measure 2 is %s, %s", 
                 hof[-1], hof[-1].fitness.values)

    return pop, stats, hof

if __name__ == "__main__":
    main()
