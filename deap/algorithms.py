from copy import deepcopy
from itertools import cycle, islice, izip
import random


def evaluate_invalids(individuals, eval_func, map):
    invalid_ind = [ind for ind in individuals if not ind.fitness.valid]
    fitnesses = map(eval_func, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    return len(invalid_ind)


def and_variation(population, toolbox, cxpb, mutpb):
    individuals = cycle(population)

    # zip(iter, iter) produces l[i], l[i+1]
    for i1, i2 in izip(individuals, individuals):
        # TODO: put deepcopy in operators
        i1, i2 = deepcopy(i1), deepcopy(i2)
        if random.random() < cxpb:
            i1, i2 = toolbox.mate(i1, i2)

        if random.random() < mutpb:
            i1, = toolbox.mutate(i1)

        if random.random() < mutpb:
            i2, = toolbox.mutate(i2)

        del i1.fitness.values, i2.fitness.values

        yield i1
        yield i2


def or_variation(population, toolbox, cxpb, mutpb):
    assert (cxpb + mutpb) <= 1.0, (
        "The sum of the crossover and mutation probabilities must be smaller "
        "or equal to 1.0."
    )

    while True:
        op_choice = random.random()
        if op_choice < cxpb:  # Apply crossover
            i1, i2 = random.sample(population, 2)
            i1, i2 = deepcopy(i1), deepcopy(i2)
            i1, _ = toolbox.mate(i1, i2)
            del i1.fitness.values
        elif op_choice < cxpb + mutpb:  # Apply mutation
            i1 = deepcopy(random.choice(population))
            i1, = toolbox.mutate(i1)
            del i1.fitness.values
        else:  # Apply reproduction
            i1 = deepcopy(random.choice(population))

        yield i1


class SimpleAlgorithm:
    def __init__(self, population, toolbox, cxpb, mutpb):
        self.population = population
        self.toolbox = toolbox
        self.cxpb = cxpb
        self.mutpb = mutpb
        self.nevals = 0

    def __iter__(self):
        return self

    def next(self):
        # Select the next generation individuals
        offspring = self.toolbox.select(self.population, len(self.population))

        # Vary the pool of individuals
        offspring = list(islice(
            and_variation(offspring, self.toolbox, self.cxpb, self.mutpb),
            len(self.population)
        ))

        # Evaluate the new individuals
        self.nevals = evaluate_invalids(offspring, self.toolbox.evaluate, self.toolbox.map)

        # Replace the current population by the offspring
        self.population = offspring

        return self


class MuLambdaAlgorithm:
    def __init__(self, population, toolbox, selection_type, lambda_, cxpb, mutpb):
        self.population = population
        self.toolbox = toolbox
        self.selection_type = selection_type
        self.lambda_ = lambda_
        self.cxpb = cxpb
        self.mutpb = mutpb
        self.nevals = 0

        assert selection_type in {"plus", "comma", "+", ","}, (
            "Selection type must be in {'plus', 'comma'}, "
            " {} provided"
        ).format(selection_type)

    def __iter__(self):
        return self

    def next(self):
        # Vary the population
        offspring = list(islice(
            or_variation(self.population, self.toolbox, self.cxpb, self.mutpb),
            self.lambda_
        ))

        # Evaluate the new individuals
        self.nevals = evaluate_invalids(offspring, self.toolbox.evaluate, self.toolbox.map)

        if self.selection_type in {"plus", "+"}:
            offspring = self.population + offspring

        # Select the next generation population
        self.population = self.toolbox.select(offspring, len(self.population))

        return self


class GenerateUpdateAlgorithm:
    def __init__(self, toolbox):
        self.toolbox = toolbox
        self.nevals = 0

    def __iter__(self):
        return self

    def next(self):
        # Generate a new population
        self.population = self.toolbox.generate()

        # Evaluate the new individuals
        self.nevals = evaluate_invalids(self.population, self.toolbox.evaluate, self.toolbox.map)

        # Update the strategy with the evaluated individuals
        self.toolbox.update(self.population)

        return self
