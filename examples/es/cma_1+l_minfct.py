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

import numpy

from deap import algorithms
from deap import base
from deap import benchmarks
from deap import cma
from deap import creator
from deap import tools

N=5
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

# See http://www.lri.fr/~hansen/cmaes_inmatlab.html for more details about
# the rastrigin and other tests for CMA-ES
toolbox = base.Toolbox()
toolbox.register("evaluate", benchmarks.sphere)

def main():
    numpy.random.seed()

    # The CMA-ES One Plus Lambda algorithm takes a initialized parent as argument
    parent = creator.Individual((numpy.random.rand() * 5) - 1 for _ in range(N))
    parent.fitness.values = toolbox.evaluate(parent)
    
    strategy = cma.StrategyOnePlusLambda(parent, sigma=5.0, lambda_=10)
    toolbox.register("generate", strategy.generate, ind_init=creator.Individual)
    toolbox.register("update", strategy.update)

    hof = tools.HallOfFame(1)    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
   
    algorithms.eaGenerateUpdate(toolbox, ngen=200, halloffame=hof, stats=stats)

if __name__ == "__main__":
    main()
