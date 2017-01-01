"""Test functions from deap/benchmarks."""
import sys
import unittest
from nose import with_setup
from past.builtins import xrange

from deap import base
from deap import benchmarks
from deap import creator
from deap.benchmarks import binary


class BenchmarkTest(unittest.TestCase):
    """Test object for unittest of deap/benchmarks."""

    def setUp(self):

        @binary.bin2float(0, 1023, 10)
        def evaluate(individual):
            """Simplest evaluation function."""
            return individual

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        self.toolbox = base.Toolbox()
        self.toolbox.register("evaluate", evaluate)

    def tearDown(self):
        del creator.FitnessMin

    def test_bin2float(self):

        # Correct evaluation of bin2float.
        zero_individual = creator.Individual([0 for x in xrange(10)])
        full_individual = creator.Individual([1 for x in xrange(10)])
        two_individiual = creator.Individual(8*[0] + [1, 0])
        population = [zero_individual, full_individual, two_individiual]
        fitnesses = map(self.toolbox.evaluate, population)
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        assert population[0].fitness.values == (0.0, )
        assert population[1].fitness.values == (1023.0, )
        assert population[2].fitness.values == (2.0, )

        # Incorrect evaluation of bin2float.
        wrong_size_individual = creator.Individual([0, 1, 0, 1, 0, 1, 0, 1, 1])
        wrong_population = [wrong_size_individual]
        # It is up the user to make sure that bin2float gets an individual with
        # an adequate length; no exceptions are raised.
        fitnesses = map(self.toolbox.evaluate, wrong_population)
        for ind, fit in zip(wrong_population, fitnesses):
            # In python 2.7 operator.mul works in a different way than in
            # python3. Thus an error occurs in python2.7 but an assignment is
            # correctly executed in python3.
            if sys.version_info < (3, ):
                with self.assertRaises(TypeError):
                    ind.fitness.values = fit
            else:
                assert wrong_population[0].fitness.values == ()


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(BenchmarkTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
