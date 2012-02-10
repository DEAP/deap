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
import numpy
import random

from deap import base
from deap import benchmarks
from deap import cma
from deap import creator
from deap import tools

N=30
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

# The centroid is set to a vector of 5.0 see http://www.lri.fr/~hansen/cmaes_inmatlab.html
# for more details about the rastrigin and other tests for CMA-ES
toolbox = base.Toolbox()
toolbox.register("attr", random.uniform, -1, 5)
toolbox.register("evaluate", benchmarks.rastrigin)

def main():
    random.seed(64)
    numpy.random.seed(64)

    # The CMA-ES algorithm takes a population of one individual as argument
    parent = tools.initRepeat(creator.Individual, toolbox.attr, N)
    parent.fitness.values = toolbox.evaluate(parent)
    
    strategy = cma.CMA1pLStrategy(parent, sigma=5.0, lambda_=8)
    toolbox.register("update", strategy.update)
    pop = strategy.generate(creator.Individual)
    
    hof = tools.HallOfFame(1)    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", tools.mean)
    stats.register("Std", tools.std)
    stats.register("Min", min)
    stats.register("Max", max)
    logger = tools.EvolutionLogger(stats.functions.keys())
   
    # The CMA-ES algorithm converge with good probability with those settings
    cma.esCMA(toolbox, pop, ngen=600, halloffame=hof, statistics=stats,
              logger=logger)

if __name__ == "__main__":
    main()
