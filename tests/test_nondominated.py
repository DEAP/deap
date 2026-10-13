import pytest

from deap import base
from deap import creator
from deap import tools


@pytest.fixture(params=[-1.0, 1.0])
def single_objective_population(request):
    creator.create("SingleObjectiveFitness", base.Fitness,
                   weights=(request.param,))
    creator.create("SingleObjectiveIndividual", list,
                   fitness=creator.SingleObjectiveFitness)
    population = [creator.SingleObjectiveIndividual([value])
                  for value in [4, 1, 3, 1, 2, 3]]
    for individual in population:
        individual.fitness.values = individual
    fronts = [[population[1], population[3]], [population[4]],
              [population[2], population[5]], [population[0]]]
    if request.param > 0:
        fronts.reverse()
    yield population, fronts
    del creator.SingleObjectiveFitness
    del creator.SingleObjectiveIndividual


@pytest.mark.parametrize("k", [0, 1, 3, 6])
@pytest.mark.parametrize("first_front_only", [False, True])
def test_log_sort_single_objective(single_objective_population, k,
                                   first_front_only):
    population, fronts = single_objective_population
    expected = []
    count = 0
    if first_front_only and k:
        expected = fronts[0]
    elif k:
        for front in fronts:
            expected.append(front)
            count += len(front)
            if count >= k:
                break

    actual = tools.sortLogNondominated(population, k, first_front_only)
    assert actual == expected


@pytest.mark.parametrize("selector", ["nsga2", "nsga3", "nsga3_memory"])
@pytest.mark.parametrize("k", [2, 5])
def test_selection_single_objective(single_objective_population, selector, k):
    population, fronts = single_objective_population
    expected = sorted(ind[0] for front in fronts for ind in front)
    if population[0].fitness.weights[0] > 0:
        expected.reverse()
    expected = sorted(expected[:k])

    if selector == "nsga2":
        selected = tools.selNSGA2(population, k, nd="log")
    else:
        ref_points = tools.uniform_reference_points(nobj=1, p=12)
        if selector == "nsga3":
            selected = tools.selNSGA3(population, k, ref_points)
        else:
            select = tools.selNSGA3WithMemory(ref_points)
            selected = select(population, k)
            assert sorted(ind[0] for ind in select(population, k)) == expected

    assert len(selected) == k
    assert sorted(ind[0] for ind in selected) == expected
    assert all(any(ind is original for original in population)
               for ind in selected)
