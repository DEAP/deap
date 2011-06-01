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
import sys
import random

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from deap import algorithms
from deap import base
from deap import benchmarks
from deap import creator
from deap import operators
from deap import toolbox

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_float", random.uniform, -5, 5)

# Structure initializers
tools.register("individual", toolbox.fillRepeat, creator.Individual, tools.attr_float, 3)
tools.register("population", toolbox.fillRepeat, list, tools.individual)

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

tools.register("evaluate", benchmarks.kursawe)
tools.register("mate", operators.cxBlend, alpha=1.5)
tools.register("mutate", operators.mutGaussian, mu=0, sigma=3, indpb=0.3)
tools.register("select", operators.selNSGA2)

tools.decorate("mate", checkBounds(-5, 5))
tools.decorate("mutate", checkBounds(-5, 5)) 

def main():
    random.seed(64)

    MU, LAMBDA = 50, 100
    pop = tools.population(n=MU)
    hof = operators.ParetoFront()
    stats = operators.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", operators.mean)
    stats.register("Std", operators.std_dev)
    stats.register("Min", min)
    stats.register("Max", max)
    
    algorithms.eaMuPlusLambda(tools, pop, mu=MU, lambda_=LAMBDA, 
                              cxpb=0.5, mutpb=0.2, ngen=50, 
                              stats=stats, halloffame=hof)
    
    logging.info("Best individual for measure 1 is %s, %s", 
                 hof[0], hof[0].fitness.values)
    logging.info("Best individual for measure 2 is %s, %s", 
                 hof[-1], hof[-1].fitness.values)

    return pop, stats, hof

if __name__ == "__main__":
    main()
