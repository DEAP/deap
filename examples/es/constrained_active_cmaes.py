
from deap import base
from deap import benchmarks
from deap import creator
from deap import tools
from deap.cma import ActiveOnePlusLambdaStrategy
import numpy

N = 5

creator.create("Fitness", base.ConstrainedFitness, weights=(-1.0,))
creator.create("Ind", list, fitness=creator.Fitness)


def constraint_1(individual):
    if individual[0] + individual[1] < 0.1:
        return True
    return False


def constraint_2(individual):
    if individual[3] < 0.1:
        return True
    return False


def evaluate_constraints(individual):
    return tuple(fc(individual) for fc in [constraint_1, constraint_2])


def populate_toolbox(strategy):
    toolbox = base.Toolbox()
    toolbox.register("evaluate", benchmarks.sphere)
    toolbox.register("generate", strategy.generate, ind_init=creator.Ind)
    toolbox.register("update", strategy.update)
    return toolbox


def optimize(verbose=True):
    NGEN = 1500
    parent = [4] * N
    strategy = ActiveOnePlusLambdaStrategy(parent, 0.5, [0, 0, 0.1, 0, 0], lambda_=20)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals', 'num_invalids'] + (stats.fields if stats else [])

    toolbox = populate_toolbox(strategy)

    best = None

    for gen in range(NGEN):
        # Generate a new population
        population = toolbox.generate()

        # Evaluate the individuals
        for individual in population:
            constraint_violation = evaluate_constraints(individual)
            if not any(constraint_violation):
                individual.fitness.values = toolbox.evaluate(individual)
            individual.fitness.constraint_violation = constraint_violation

            if best is None or individual.fitness >= best.fitness:
                best = individual

        valid_population = [ind for ind in population if ind.fitness.valid]
        record = {}

        if valid_population:
            record = stats.compile(valid_population)
        num_invalids = sum(1 for ind in population if not ind.fitness.valid)
        logbook.record(gen=gen, nevals=len(valid_population), num_invalids=num_invalids, **record)
        if verbose:
            print(logbook.stream)

        toolbox.update(population)

        if strategy.condition_number > 10e12:
            return best

    return best


def main(verbose=True):
    restarts = 3
    best = None
    overall_best = None

    for _ in range(restarts):
        best = optimize(verbose)

        if overall_best is None \
                or (best.fitness.valid and best.fitness >= overall_best.fitness):
            overall_best = best

    print(best)
    print(best.fitness)


if __name__ == "__main__":
    main()
