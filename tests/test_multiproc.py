import multiprocessing

from deap import base
from deap import creator


def _evalOneMax(individual):
    return sum(individual),


def test_multiproc():
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("evaluate", _evalOneMax)

    # Process Pool of 4 workers
    pool = multiprocessing.Pool(processes=4)
    toolbox.register("map", pool.map)

    pop = [[1] * 20 for _ in range(100)]
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        assert fit == (sum(ind),)
