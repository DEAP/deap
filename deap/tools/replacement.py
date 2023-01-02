"""
This module defines operators for replacing individuals
at the end of a generation.
"""


def elitism(population, offspring, n_elites):
    """
    Create new population keeping a number of elites from
    the parent population.

    Note: this selection mechanism works only for single-objective
    problems.
    """
    sorted_offspring = sorted(offspring, key=lambda x: x.fitness.values)
    sorted_population = sorted(population, key=lambda x: x.fitness.values)

    for i in range(n_elites):
        pop_idx = -n_elites + i
        if sorted_offspring[i].fitness < sorted_population[pop_idx]:
            sorted_offspring[i] = sorted_population[pop_idx]
    return sorted_offspring
