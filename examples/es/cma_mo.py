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
# from deap import cma
import cma
from deap import creator
from deap import tools

# Problem size
N = 30

ZDT1_MIN = numpy.zeros(N)
ZDT1_MAX = numpy.ones(N)

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

def distance(feasible_ind, original_ind):
    """A distance function to the feasability region."""
    return sum((f - o)**2 for f, o in zip(feasible_ind, original_ind))

def feasible(individual):
    """A function return a valid individual from an invalid one."""
    feasible_ind = numpy.array(individual)
    feasible_ind = numpy.maximum(MIN_BOUND, feasible_ind)
    feasible_ind = numpy.minimum(MAX_BOUND, feasible_ind)
    return feasible_ind

def feasiblility(individual):
    """Determines if the individual is valid or not."""
    if any(individual < ZDT1_MIN) or any(individual > ZDT1_MAX):
        return False
    return True

toolbox = base.Toolbox()
toolbox.register("evaluate", benchmarks.zdt1)
toolbox.decorate("evaluate", tools.ClosestPenality(feasiblility, feasible, 1.0e-6, distance))

def main():
    # The cma module uses the numpy random number generator
    # numpy.random.seed(128)

    MU, LAMBDA = 100, 100

    # The MO-CMA-ES algorithm takes a full population as argument
    pop = numpy.random.rand(MU, N)
    strategy = cma.StrategyMultiObjective(pop, sigma=0.6, mu=MU, lambda_=LAMBDA)
    toolbox.register("generate", strategy.generate, creator.Individual)
    toolbox.register("update", strategy.update)

    hof = tools.ParetoFront()
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
   
    # The CMA-ES algorithm converge with good probability with those settings
    algorithms.eaGenerateUpdate(toolbox, ngen=250, stats=stats, halloffame=hof)
    
    return hof

if __name__ == "__main__":
    hof = main()

    import matplotlib.pyplot as plt

    front = numpy.array([ind.fitness.values for ind in hof])
    plt.scatter(front[:,0], front[:,1], c="b")
    plt.axis("tight")
    plt.show()
