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

from nose import with_setup
import random

import numpy

from deap import algorithms
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import hypervolume
from deap import cma
from deap import creator
from deap import tools

FITCLSNAME = "FIT_TYPE"
INDCLSNAME = "IND_TYPE"

HV_THRESHOLD = 116.0        # 120.777 is Optimal value


def setup_func_single_obj():
    creator.create(FITCLSNAME, base.Fitness, weights=(-1.0,))
    creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

def setup_func_multi_obj():
    creator.create(FITCLSNAME, base.Fitness, weights=(-1.0, -1.0))
    creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

def setup_func_multi_obj_numpy():
    creator.create(FITCLSNAME, base.Fitness, weights=(-1.0, -1.0))
    creator.create(INDCLSNAME, numpy.ndarray, fitness=creator.__dict__[FITCLSNAME])

def teardown_func():
    # Messy way to remove a class from the creator
    del creator.__dict__[FITCLSNAME]
    del creator.__dict__[INDCLSNAME]

@with_setup(setup_func_single_obj, teardown_func)
def test_cma():
    NDIM = 5

    strategy = cma.Strategy(centroid=[0.0]*NDIM, sigma=1.0)

    toolbox = base.Toolbox()
    toolbox.register("evaluate", benchmarks.sphere)
    toolbox.register("generate", strategy.generate, creator.__dict__[INDCLSNAME])
    toolbox.register("update", strategy.update)

    pop, _ = algorithms.eaGenerateUpdate(toolbox, ngen=100)
    best, = tools.selBest(pop, k=1)

    assert best.fitness.values < (1e-8,), "CMA algorithm did not converged properly."

@with_setup(setup_func_multi_obj, teardown_func)
def test_nsga2():
    NDIM = 5
    BOUND_LOW, BOUND_UP = 0.0, 1.0
    MU = 16
    NGEN = 100

    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.uniform, BOUND_LOW, BOUND_UP)
    toolbox.register("individual", tools.initRepeat, creator.__dict__[INDCLSNAME], toolbox.attr_float, NDIM)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", benchmarks.zdt1)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
    toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)
    toolbox.register("select", tools.selNSGA2)

    pop = toolbox.population(n=MU)
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    pop = toolbox.select(pop, len(pop))
    for gen in range(1, NGEN):
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() <= 0.9:
                toolbox.mate(ind1, ind2)

            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.fitness.values, ind2.fitness.values

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop = toolbox.select(pop + offspring, MU)

    hv = hypervolume(pop, [11.0, 11.0])
    # hv = 120.777 # Optimal value

    assert hv > HV_THRESHOLD, "Hypervolume is lower than expected %f < %f" % (hv, HV_THRESHOLD)

    for ind in pop:
        assert not (any(numpy.asarray(ind) < BOUND_LOW) or any(numpy.asarray(ind) > BOUND_UP))


@with_setup(setup_func_multi_obj_numpy, teardown_func)
def test_mo_cma_es():

    def distance(feasible_ind, original_ind):
        """A distance function to the feasibility region."""
        return sum((f - o)**2 for f, o in zip(feasible_ind, original_ind))

    def closest_feasible(individual):
        """A function returning a valid individual from an invalid one."""
        feasible_ind = numpy.array(individual)
        feasible_ind = numpy.maximum(BOUND_LOW, feasible_ind)
        feasible_ind = numpy.minimum(BOUND_UP, feasible_ind)
        return feasible_ind

    def valid(individual):
        """Determines if the individual is valid or not."""
        if any(individual < BOUND_LOW) or any(individual > BOUND_UP):
            return False
        return True

    NDIM = 5
    BOUND_LOW, BOUND_UP = 0.0, 1.0
    MU, LAMBDA = 10, 10
    NGEN = 500

    numpy.random.seed(128)

    # The MO-CMA-ES algorithm takes a full population as argument
    population = [creator.__dict__[INDCLSNAME](x) for x in numpy.random.uniform(BOUND_LOW, BOUND_UP, (MU, NDIM))]

    toolbox = base.Toolbox()
    toolbox.register("evaluate", benchmarks.zdt1)
    toolbox.decorate("evaluate", tools.ClosestValidPenalty(valid, closest_feasible, 1.0e+6, distance))

    for ind in population:
        ind.fitness.values = toolbox.evaluate(ind)

    strategy = cma.StrategyMultiObjective(population, sigma=1.0, mu=MU, lambda_=LAMBDA)

    toolbox.register("generate", strategy.generate, creator.__dict__[INDCLSNAME])
    toolbox.register("update", strategy.update)

    for gen in range(NGEN):
        # Generate a new population
        population = toolbox.generate()

        # Evaluate the individuals
        fitnesses = toolbox.map(toolbox.evaluate, population)
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit

        # Update the strategy with the evaluated individuals
        toolbox.update(population)

    # Note that we use a penalty to guide the search to feasible solutions,
    # but there is no guarantee that individuals are valid.
    # We expect the best individuals will be within bounds or very close.
    num_valid = 0
    for ind in strategy.parents:
        dist = distance(closest_feasible(ind), ind)
        if numpy.isclose(dist, 0.0, rtol=1.e-5, atol=1.e-5):
            num_valid += 1
    assert num_valid >= len(strategy.parents)

    # Note that NGEN=500 is enough to get consistent hypervolume > 116,
    # but not 119. More generations would help but would slow down testing.
    hv = hypervolume(strategy.parents, [11.0, 11.0])
    assert hv > HV_THRESHOLD, "Hypervolume is lower than expected %f < %f" % (hv, HV_THRESHOLD)


@with_setup(setup_func_multi_obj, teardown_func)
def test_nsga3():
    NDIM = 5
    BOUND_LOW, BOUND_UP = 0.0, 1.0
    MU = 16
    NGEN = 100

    ref_points = tools.uniform_reference_points(2, p=12)

    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.uniform, BOUND_LOW, BOUND_UP)
    toolbox.register("individual", tools.initRepeat, creator.__dict__[INDCLSNAME], toolbox.attr_float, NDIM)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", benchmarks.zdt1)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
    toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)
    toolbox.register("select", tools.selNSGA3, ref_points=ref_points)

    pop = toolbox.population(n=MU)
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    pop = toolbox.select(pop, len(pop))
     # Begin the generational process
    for gen in range(1, NGEN):
        offspring = algorithms.varAnd(pop, toolbox, 1.0, 1.0)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Select the next generation population
        pop = toolbox.select(pop + offspring, MU)

    hv = hypervolume(pop, [11.0, 11.0])
    # hv = 120.777 # Optimal value

    assert hv > HV_THRESHOLD, "Hypervolume is lower than expected %f < %f" % (hv, HV_THRESHOLD)

    for ind in pop:
        assert not (any(numpy.asarray(ind) < BOUND_LOW) or any(numpy.asarray(ind) > BOUND_UP))
