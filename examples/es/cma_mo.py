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
from deap.benchmarks.tools import hypervolume
from deap import cma
from deap import creator
from deap import tools

# Problem size
N = 5

# ZDT1, ZDT2, DTLZ2
MIN_BOUND = numpy.zeros(N)
MAX_BOUND = numpy.ones(N)

# Kursawe
# MIN_BOUND = numpy.zeros(N) - 5
# MAX_BOUND = numpy.zeros(N) + 5

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMin)

def distance(feasible_ind, original_ind):
    """A distance function to the feasibility region."""
    return sum((f - o)**2 for f, o in zip(feasible_ind, original_ind))

def closest_feasible(individual):
    """A function returning a valid individual from an invalid one."""
    feasible_ind = numpy.array(individual)
    feasible_ind = numpy.maximum(MIN_BOUND, feasible_ind)
    feasible_ind = numpy.minimum(MAX_BOUND, feasible_ind)
    return feasible_ind

def valid(individual):
    """Determines if the individual is valid or not."""
    if any(individual < MIN_BOUND) or any(individual > MAX_BOUND):
        return False
    return True

toolbox = base.Toolbox()
toolbox.register("evaluate", benchmarks.zdt1)
toolbox.decorate("evaluate", tools.ClosestValidPenalty(valid, closest_feasible, 1.0e-6, distance))

def main():
    # The cma module uses the numpy random number generator
    # numpy.random.seed(128)

    MU, LAMBDA = 10, 10
    NGEN = 500
    verbose = True

    # The MO-CMA-ES algorithm takes a full population as argument
    population = [creator.Individual(x) for x in (numpy.random.uniform(0, 1, (MU, N)))]

    for ind in population:
        ind.fitness.values = toolbox.evaluate(ind)

    strategy = cma.StrategyMultiObjective(population, sigma=1.0, mu=MU, lambda_=LAMBDA)
    toolbox.register("generate", strategy.generate, creator.Individual)
    toolbox.register("update", strategy.update)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)
   
    logbook = tools.Logbook()
    logbook.header = ["gen", "nevals"] + (stats.fields if stats else [])

    for gen in range(NGEN):
        # Generate a new population
        population = toolbox.generate()

        # Evaluate the individuals
        fitnesses = toolbox.map(toolbox.evaluate, population)
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        
        # Update the strategy with the evaluated individuals
        toolbox.update(population)
        
        record = stats.compile(population) if stats is not None else {}
        logbook.record(gen=gen, nevals=len(population), **record)
        if verbose:
            print(logbook.stream)

    if verbose:
        print("Final population hypervolume is %f" % hypervolume(strategy.parents, [11.0, 11.0]))
    
    # import matplotlib.pyplot as plt
    
    # valid_front = numpy.array([ind.fitness.values for ind in strategy.parents if valid(ind)])
    # invalid_front = numpy.array([ind.fitness.values for ind in strategy.parents if not valid(ind)])

    # fig = plt.figure()

    # if len(valid_front) > 0:
    #     plt.scatter(valid_front[:,0], valid_front[:,1], c="g")

    # if len(invalid_front) > 0:
    #     plt.scatter(invalid_front[:,0], invalid_front[:,1], c="r")

    # plt.show()
    
    return strategy.parents

if __name__ == "__main__":
    solutions = main()
