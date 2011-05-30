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
import sys
import random
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
# random.seed(64)     # Random must be seeded before importing cma because it is
                    # used to seed numpy.random
                    # This will be fixed in future release.

from deap import base
from deap import cma
from deap import creator
from deap import operators
from deap import toolbox

from deap import benchmarks
N=5
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

# The centroid is set to a vector of 5.0 see http://www.lri.fr/~hansen/cmaes_inmatlab.html
# for more details about the rastrigin and other tests for CMA-ES
tools = toolbox.Toolbox()
tools.register("attr", random.uniform, -1, 5)
tools.register("evaluate", benchmarks.ackley)

def main():
    # The CMA-ES algorithm takes a population of one individual as argument
    
    parent = toolbox.fillRepeat(creator.Individual, tools.attr, N)
    parent.fitness.values = tools.evaluate(parent)
    strategy = cma.CMA11Strategy(parent, sigma=5.0)
    tools.register("update", strategy.update)
    pop = strategy.generate(creator.Individual)
    
    hof = operators.HallOfFame(1)    
    stats = operators.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", operators.mean)
    stats.register("Std", operators.std_dev)
    stats.register("Min", min)
    stats.register("Max", max)
   
    # The CMA-ES algorithm converge with good probability with those settings
    cma.esCMA(tools, pop, ngen=600, halloffame=hof, statistics=stats)
    
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)

if __name__ == "__main__":
    main()
