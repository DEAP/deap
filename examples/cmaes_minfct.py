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
from deap import benchmarks
from deap import cma
from deap import creator
from deap import tools

# Problem size
N=30

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("evaluate", benchmarks.rastrigin)

def main():
    # The CMA-ES algorithm takes a population of one individual as argument
    # The centroid is set to a vector of 5.0 see http://www.lri.fr/~hansen/cmaes_inmatlab.html
    # for more details about the rastrigin and other tests for CMA-ES    
    strategy = cma.CMAStrategy(centroid=[5.0]*N, sigma=5.0, lambda_=20*N)
    pop = strategy.generate(creator.Individual)
    hof = tools.HallOfFame(1)
    toolbox.register("update", strategy.update)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", tools.mean)
    stats.register("Std", tools.std)
    stats.register("Min", min)
    stats.register("Max", max)
   
    # The CMA-ES algorithm converge with good probability with those settings
    cma.esCMA(toolbox, pop, ngen=250, halloffame=hof, statistics=stats)
    
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)

if __name__ == "__main__":
    main()
