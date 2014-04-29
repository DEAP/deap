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
N = 30

# ZDT1, ZDT2, DTLZ2
MIN_BOUND = numpy.zeros(N)
MAX_BOUND = numpy.ones(N)

# Kursawe
# MIN_BOUND = numpy.zeros(N) - 5
# MAX_BOUND = numpy.zeros(N) + 5

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMin)

def distance(feasible_ind, original_ind):
    """A distance function to the feasability region."""
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
toolbox.register("evaluate", benchmarks.dtlz2, obj=2)
toolbox.decorate("evaluate", tools.ClosestValidPenality(valid, closest_feasible, 1.0e-6, distance))

def main():
    # The cma module uses the numpy random number generator
    # numpy.random.seed(128)

    invalid_count = 0
    distances = list()

    MU, LAMBDA = 100, 100
    NGEN = 500
    verbose = False

    # The MO-CMA-ES algorithm takes a full population as argument
    population = [creator.Individual(x) for x in (numpy.random.uniform(0, 1, (MU + LAMBDA, N)))]
    # init = numpy.zeros((MU, N))
    # init[:, 0] = numpy.linspace(0, 1, 100)
    # population = [creator.Individual(x) for x in init]
    for ind in population:
        ind.fitness.values = toolbox.evaluate(ind)

    strategy = cma.StrategyMultiObjective(population, sigma=1.0, mu=MU, lambda_=LAMBDA)
    toolbox.register("generate", strategy.generate, creator.Individual)
    toolbox.register("update", strategy.update)

    halloffame = tools.ParetoFront()
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    # stats.register("avg", numpy.mean, axis=0)
    # stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)
   
    # The CMA-ES algorithm converge with good probability with those settings
    logbook = tools.Logbook()
    logbook.header = ["gen", "nevals"] + (stats.fields if stats else [])

    sigmas = numpy.zeros((MU, NGEN))

    for gen in range(NGEN):
        # Generate a new population
        population = toolbox.generate()
        # Evaluate the individuals
        fitnesses = toolbox.map(toolbox.evaluate, population)
        for ind, fit in zip(population, fitnesses):
            if not valid(ind):
                invalid_count += 1
                f_ind = closest_feasible(ind)
                distances.append(distance(f_ind, ind))
                # print("Valid fitness:", toolbox.evaluate(f_ind))
                # print("Invalid fitness:", fit)
            ind.fitness.values = fit
        
        if halloffame is not None:
            halloffame.update(population)
        
        # Update the strategy with the evaluated individuals
        toolbox.update(population)

        sigmas[:, gen] = strategy.sigmas
        
        record = stats.compile(population) if stats is not None else {}
        logbook.record(gen=gen, nevals=len(population), **record)
        if verbose:
            print(logbook.stream)

        print("invalids", invalid_count)
        print("distance", numpy.average(distances))
        distances = list()
        # print("sigma", numpy.average(sigmas[:, gen]))

        print("success", strategy.success_count)

    import matplotlib.pyplot as plt
    # from mpl_toolkits.mplot3d import Axes3D
    
    valid_front = numpy.array([ind.fitness.values for ind in population if valid(ind)])
    invalid_front = numpy.array([ind.fitness.values for ind in population if not valid(ind)])
    
    fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(front[:,0], front[:,1], front[:,2], c="b")
    
    plt.scatter(valid_front[:,0], valid_front[:,1], c="g")
    plt.scatter(invalid_front[:,0], invalid_front[:,1], c="r")

    plt.figure()
    sigmas = numpy.mean(sigmas, axis=0)
    plt.plot(sigmas)

    plt.show()
    
    return halloffame

if __name__ == "__main__":
    hof = main()

    

    