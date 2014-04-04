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

# Problem size
N = 3

# ZDT1, ZDT2, 
# MIN_BOUND = numpy.zeros(N)
# MAX_BOUND = numpy.ones(N)

# Kursawe
MIN_BOUND = numpy.zeros(N) - 5
MAX_BOUND = numpy.zeros(N) + 5

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
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
    if any(individual < MIN_BOUND) or any(individual > MAX_BOUND):
        return False
    return True

toolbox = base.Toolbox()
toolbox.register("evaluate", benchmarks.kursawe)
toolbox.decorate("evaluate", tools.ClosestPenality(feasiblility, feasible, 1.0e-6, distance))

def main():
    # The cma module uses the numpy random number generator
    # numpy.random.seed(128)

    MU, LAMBDA = 100, 100

    # The MO-CMA-ES algorithm takes a full population as argument
    pop = [creator.Individual(x) for x in numpy.random.rand(MU, N)]
    for ind in pop:
        ind.fitness.values = toolbox.evaluate(ind)

    strategy = cma.StrategyMultiObjective(pop, sigma=0.6, mu=MU, lambda_=LAMBDA)
    toolbox.register("generate", strategy.generate, creator.Individual)
    toolbox.register("update", strategy.update)

    hof = tools.ParetoFront()
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)
   
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
