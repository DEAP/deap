from copy import deepcopy
from itertools import cycle, islice
import random


def and_variation(population, toolbox, cxpb, mutpb):
    individuals = cycle(population)
    left, right = individuals, individuals
    for i1, i2 in zip(left, right):
        # TODO: put deepcopy in operators
        i1, i2 = deepcopy([i1, i2])
        if random.random() < cxpb:
            i1, i2 = toolbox.mate(i1, i2)

        if random.random() < mutpb:
            i1, = toolbox.mutate(i1)

        if random.random() < mutpb:
            i2, = toolbox.mutate(i2)

        del i1.fitness.values, i2.fitness.values

        yield i1, i2


class SimpleAlgorithm:
    def __init__(self, population, toolbox, cxpb, mutpb):
        self.population = population
        self.toolbox = toolbox
        self.cxpb = cxpb
        self.mutpb = mutpb

    def __iter__(self):
        return self

    def __next__(self):
        # Select the next generation individuals
        offspring = self.toolbox.select(self.population, len(self.population))

        # Vary the pool of individuals
        offspring = [
            islice(
                and_variation(offspring, self.toolbox, self.cxpb, self.mutpb),
                len(self.population)
            )
        ]

        # Evaluate the new individuals
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Replace the current population by the offspring
        self.population[:] = offspring

        return self
