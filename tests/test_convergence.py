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

from itertools import islice
import random
import unittest

try:
    import numpy
except ImportError:
    numpy = False

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


class TearDownCreatorTestCase(unittest.TestCase):
    def tearDown(self):
        # Messy way to remove a class from the creator
        del creator.__dict__[FITCLSNAME]
        del creator.__dict__[INDCLSNAME]


class TestSingleObjective(TearDownCreatorTestCase):
    def setUp(self):
        creator.create(FITCLSNAME, base.Fitness, weights=(-1.0,))
        creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

    def test_cma(self):
        NDIM = 5
        NGEN = 100

        strategy = cma.Strategy(centroid=[0.0] * NDIM, sigma=1.0)

        toolbox = base.Toolbox()
        toolbox.register("evaluate", benchmarks.sphere)
        toolbox.register("generate", strategy.generate, creator.__dict__[INDCLSNAME])
        toolbox.register("update", strategy.update)

        # Consume the algorithm until NGEN
        population, _ = algorithms.eaGenerateUpdate(toolbox, NGEN)

        best, = tools.selBest(population, k=1)

        self.assertLess(best.fitness.values[0], 1e-8)

    def test_cma_mixed_integer_1_p_1_no_constraint(self):
        N = 3
        NGEN = 15000

        toolbox = base.Toolbox()
        toolbox.register("evaluate", benchmarks.sphere)

        parent = (numpy.random.rand(N) * 2) + 1

        strategy = cma.StrategyActiveOnePlusLambda(parent, 0.5, [0, 0, 0.1], lambda_=1)

        toolbox.register("generate", strategy.generate, ind_init=creator.__dict__[INDCLSNAME])
        toolbox.register("update", strategy.update)

        best = None

        for gen in range(NGEN):
            # Generate a new population
            population = toolbox.generate()

            # Evaluate the individuals
            for individual in population:
                individual.fitness.values = toolbox.evaluate(individual)

                if best is None or individual.fitness >= best.fitness:
                    best = individual

            # We must stop CMA-ES before the update becomes unstable
            if best.fitness.values[0] < 1e-12:
                break

            # Update the strategy with the evaluated individuals
            toolbox.update(population)

        self.assertLess(best.fitness.values[0], 1e-12)

    def test_cma_mixed_integer_1_p_20_no_constraint(self):
        N = 3
        NGEN = 15000

        toolbox = base.Toolbox()
        toolbox.register("evaluate", benchmarks.sphere)

        parent = (numpy.random.rand(N) * 2) + 1

        strategy = cma.StrategyActiveOnePlusLambda(parent, 0.5, [0, 0, 0.1], lambda_=20)

        toolbox.register("generate", strategy.generate, ind_init=creator.__dict__[INDCLSNAME])
        toolbox.register("update", strategy.update)

        best = None

        for gen in range(NGEN):
            # Generate a new population
            population = toolbox.generate()

            # Evaluate the individuals
            for individual in population:
                individual.fitness.values = toolbox.evaluate(individual)

                if best is None or individual.fitness >= best.fitness:
                    best = individual

            # Stop when we've reached some kind of optimum
            if best.fitness.values[0] < 1e-12:
                break

            # Update the strategy with the evaluated individuals
            toolbox.update(population)

        self.assertLess(best.fitness.values[0], 1e-12)


class TestSingleObjectiveConstrained(TearDownCreatorTestCase):
    def setUp(self):
        creator.create(FITCLSNAME, base.ConstrainedFitness, weights=(-1.0,))
        creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

    def test_cma_mixed_integer_1_p_1_with_constraint(self):
        def c1(individual):
            if individual[0] + individual[1] < 0.1:
                return True
            return False

        def c2(individual):
            if individual[1] < 0.1:
                return True
            return False

        N = 5
        NGEN = 15000
        optimum = 0.015

        toolbox = base.Toolbox()
        toolbox.register("evaluate", benchmarks.sphere)
        restarts = 10

        # Allow a couple of restarts
        while restarts > 0:
            parent = (numpy.random.rand(N) * 2) + 1

            strategy = cma.StrategyActiveOnePlusLambda(parent, 0.5, [0, 0, 0.1, 0, 0], lambda_=1)

            toolbox.register("generate", strategy.generate, ind_init=creator.__dict__[INDCLSNAME])
            toolbox.register("update", strategy.update)

            best = None

            for gen in range(NGEN):
                # Generate a new population
                population = toolbox.generate()

                # Evaluate the individuals
                for individual in population:
                    constraint_violation = c1(individual), c2(individual)
                    if not any(constraint_violation):
                        individual.fitness.values = toolbox.evaluate(individual)
                    individual.fitness.constraint_violation = constraint_violation

                    if best is None or individual.fitness >= best.fitness:
                        best = individual

                # Stop when we've reached some kind of optimum
                if best.fitness.values[0] - optimum < 1e-7:
                    restarts = 0
                    break

                # Update the strategy with the evaluated individuals
                toolbox.update(population)

                if strategy.condition_number > 10e12:
                    # We've become unstable
                    break

            restarts -= 1

        self.assertLess(best.fitness.values[0] - optimum, 1e-7)

    def test_cma_mixed_integer_1_p_20_with_constraint(self):
        def c1(individual):
            if individual[0] + individual[1] < 0.1:
                return True
            return False

        def c2(individual):
            if individual[3] < 0.1:
                return True
            return False

        N = 5
        NGEN = 15000
        optimum = 0.015

        toolbox = base.Toolbox()
        toolbox.register("evaluate", benchmarks.sphere)
        restarts = 10

        # Allow a couple of restarts
        while restarts > 0:
            parent = (numpy.random.rand(N) * 2) + 1

            strategy = cma.StrategyActiveOnePlusLambda(parent, 0.5, [0, 0, 0.1, 0, 0], lambda_=20)

            toolbox.register("generate", strategy.generate, ind_init=creator.__dict__[INDCLSNAME])
            toolbox.register("update", strategy.update)

            best = None

            for gen in range(NGEN):
                # Generate a new population
                population = toolbox.generate()

                # Evaluate the individuals
                for individual in population:
                    constraint_violation = c1(individual), c2(individual)
                    if not any(constraint_violation):
                        individual.fitness.values = toolbox.evaluate(individual)
                    individual.fitness.constraint_violation = constraint_violation

                    if best is None or individual.fitness >= best.fitness:
                        best = individual

                if best.fitness.values[0] - optimum < 1e-7:
                    restarts = 0
                    break

                # Stop when we've reached some kind of optimum
                toolbox.update(population)

                if strategy.condition_number > 10e12:
                    # We've become unstable
                    break

            restarts -= 1

        self.assertLess(best.fitness.values[0] - optimum, 1e-7)


class TestMultiObjective(TearDownCreatorTestCase):
    def setUp(self):
        creator.create(FITCLSNAME, base.Fitness, weights=(-1.0, -1.0))
        creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

    def test_nsga2(self):
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
        toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0 / NDIM)
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

        self.assertGreater(hv, HV_THRESHOLD)

        for ind in pop:
            self.assertTrue(all(numpy.asarray(ind) >= BOUND_LOW))
            self.assertTrue(all(numpy.asarray(ind) <= BOUND_UP))

    def test_nsga3(self):
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
        toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0 / NDIM)
        toolbox.register("select", tools.selNSGA3, ref_points=ref_points)

        pop = toolbox.population(n=MU)
        fitnesses = toolbox.map(toolbox.evaluate, pop)
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        pop = toolbox.select(pop, len(pop))
        # Begin the generational process
        for gen in range(1, NGEN):
            # Vary the individuals
            offspring = list(islice(algorithms.varAnd(pop, toolbox, 1.0, 1.0), len(pop)))

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # Select the next generation population
            pop = toolbox.select(pop + offspring, MU)

        hv = hypervolume(pop, [11.0, 11.0])
        # hv = 120.777 # Optimal value

        self.assertGreater(hv, HV_THRESHOLD)

        for ind in pop:
            self.assertTrue(all(numpy.asarray(ind) >= BOUND_LOW))
            self.assertTrue(all(numpy.asarray(ind) <= BOUND_UP))


@unittest.skipUnless(numpy, "requires numpy")
class TestMultiObjectiveNumpy(TearDownCreatorTestCase):
    def setUp(self):
        creator.create(FITCLSNAME, base.Fitness, weights=(-1.0, -1.0))
        creator.create(INDCLSNAME, numpy.ndarray, fitness=creator.__dict__[FITCLSNAME])

    def test_mo_cma_es(self):

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
        self.assertGreaterEqual(num_valid, len(strategy.parents))

        # Note that NGEN=500 is enough to get consistent hypervolume > 116,
        # but not 119. More generations would help but would slow down testing.
        hv = hypervolume(strategy.parents, [11.0, 11.0])
        self.assertGreater(hv, HV_THRESHOLD, msg="Hypervolume is lower than expected")
