from copy import deepcopy
from itertools import cycle, islice
import random
from typing import Sequence

from .base import Individual


def evaluate_invalids(individuals: Sequence[Individual], eval_func, map=map):
    """Evaluate all individuals marked invalid.

    Args:
        individuals (iterable): Individuals to evaluate, they must have a
            :attr:`fitness` attribute. Only those with an invalid fitness
            will get evaluates.
        eval_func (callable): The evaluation to use on each individual.
            The function should take the individual as single argument.
        map (callable): Functiona that applies the evaluation function
            to each item in the invalid individuals iterable.

    Returns:
        int: The number of individuals evaluated.

    """
    invalid_ind = [ind for ind in individuals if not ind.fitness.valid]
    fitnesses = map(eval_func, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind._setfitness(None, fit)

    return len(invalid_ind)


def take(n, iterable):
    """Return first n items of an iterable as a list.

    This function is taken from Python stdlib :mod:`itertools`.
    """
    return list(islice(iterable, n))


def and_variation(population, toolbox, cxpb, mutpb):
    """Vary the individuals of a population using the operators in the toolbox.

    Iterator that generates new individuals by varying consecutive pairs of two
    individuals from the population. The variation first deepcopies the individuals
    and then applies crossover and mutation with probability *cxpb* and *mutpb* on
    each of them. Both probabilities should be in [0, 1]. The offspring are
    returned one after an other. If more individuals than the size of the population
    are requested, the population is cycled over.

    Args:
        population (Iterable): The individuals to vary.
        toolbox (base.Toolbox): The toolbox containing a *mate* and *mutate*
            method to variate the individuals.
        cxpb (float): Probability to apply crossover on every pair of individuals.
        mutpb (float): Probability to apply mutation on every individual.

    Yields:
        individual: Offspring produced by the variation.

    Example:
        The variation can generates new offspring indefinitely if required.
        To generate a given number of individual::

            >>> offspring = take(
            ...     50,
            ...     and_variation(population, toolbox, 0.6, 0.3)
            ... )       # doctest: +SKIP

    """
    individuals = cycle(population)

    # zip(iter, iter) produces l[i], l[i+1]
    for i1, i2 in zip(individuals, individuals):
        # TODO: put deepcopy in operators
        # Must deepcopy separately to ensure full deepcopy if the same
        # individual is selected twice, it is deepcopied twice (what is
        # not true with deepcopy([i1, i2])).
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
    """Vary the individuals of a population using the operators in the toolbox.

    Generates new offspring by varying the individuals of a population. At first,
    the variation selects if a crossover, a mutation or a copy should be used
    according to the given probabilities. Then, it samples randomly the appropriate
    number of individuals, 2 for crossover and 1 for mutation and copy, and
    deepcopies them before applying the operator and yields the result. *cxpb*
    and *mutpb* shoudn't sum above 1.

    Args:
        population (iterable): The individuals to vary.
        toolbox (base.Toolbox): The toolbox containing a *mate* and *mutate*
            method to variate the individuals.
        cxpb (float): Probability to apply crossover on every pair of individuals.
        mutpb (float): Probability to apply mutation on every individual.

    Yields:
        individual: Offspring produced by the variation.

    Example:
        The variation can generates new offspring indefinitely if required.
        To generate a given number of individual::

            >>> offspring = take(
            ...     50,
            ...     or_variation(population, toolbox, 0.6, 0.3)
            ... )       # doctest: +SKIP

    """
    assert (cxpb + mutpb) <= 1.0, (
        "The sum of the crossover and mutation probabilities must be smaller "
        "or equal to 1.0."
    )

    # adjust probabilities since both crossover children are appended
    cxpb_adj = cxpb / (2 - cxpb)
    if cxpb != 1.0:         # Avoid zero division
        mutpb_adj = mutpb / (mutpb + (1 - mutpb - cxpb)) * (1 - cxpb_adj)
    else:
        mutpb_adj = mutpb

    while True:
        op_choice = random.random()
        if op_choice < cxpb_adj:                # Apply crossover
            i1, i2 = random.sample(population, 2)
            # Must deepcopy separately to ensure full deepcopy if the same
            # individual is selected twice, it is deepcopied twice (what is
            # not true with deepcopy([i1, i2])).
            i1, i2 = deepcopy(i1), deepcopy(i2)
            i1, _ = toolbox.mate(i1, i2)
            del i1.fitness.values, i2.fitness.values
            offspring = [i1, i2]
        elif op_choice < cxpb_adj + mutpb_adj:  # Apply mutation
            i1 = deepcopy(random.choice(population))
            i1, = toolbox.mutate(i1)
            del i1.fitness.values
            offspring = [i1]
        else:                                   # Apply reproduction
            i1 = deepcopy(random.choice(population))
            offspring = [i1]

        for child in offspring:
            yield child


class GenerationalAlgorithm:
    """Algorithm based on a generational process.

    Each iteration, the parental population is selected from the population
    for reproduction. It is advised to use a selection with replacement as
    N individuals will be selected from a population of size N. The parents
    get to reproduce using the :func:`and_variation`.

    Args:
        population (list): Initial population for the evolution.
        toolbox (deap.base.Toolbox): Toolbox containing a *mate*,
            *mutate*, *select* and *evaluate* method.
        cxpb (float): Probability to apply crossover on every pair of individuals.
        mutpb (float): Probability to apply mutation on every individual.

    Yields:
        self

    Attributes:
        population: The population updated every generation.
        nevals: The number of evaluations in the last generation.
        toolbox
        cxpb
        mutpb

    Examples:
        This algorithm can continue the optimization indefinetely util stopped.
        Each iteration it yields itself to give access to its internal parameters.
        It can be used as follow::

            for state in GenerationAlgorithm(pop, toolbox, CXPB, MUTPB):
                if min(state.population, key=lambda ind: ind.fitness.values) < 1e-6:
                    break

        Any attribute can be changed during evolution. For example, to change the
        population, directly use the state ::

            for state in GenerationAlgorithm(pop, toolbox, CXPB, MUTPB):
                state.population = new_population()

    """
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
        offspring = take(
            len(self.population),
            and_variation(offspring, self.toolbox, self.cxpb, self.mutpb)
        )

        # Evaluate the new individuals
        self.nevals = evaluate_invalids(offspring, self.toolbox.evaluate, self.toolbox.map)

        # Replace the current population by the offspring
        self.population = offspring

        return self


class MuLambdaAlgorithm:
    r""":math:`(\mu~\begin{smallmatrix}+ \\ ,\end{smallmatrix}~\lambda)` evolutionary
    algorithm.

    Each iteration, *lambda_* individuals are produced by the :func:`or_variation`.
    The individuals are then evaluated and selection is made from the parents and
    offspring (`"+"`) or only from the offspring (`","`) depending on the input
    *selection_type*.

    Args:
        population (list): Initial population for the evolution.
        toolbox (deap.base.Toolbox): Toolbox containing a *mate*,
            *mutate*, *select* and *evaluate* method.
        selection_type (str): One of `"+", "plus", ",", or "comma"` specifying if the
            selection is made from the parents and the offspring (`"+"`) or only
            from the offspring (`","`).
        lambda_ (int): Number of individual so produce each generation.
        cxpb (float): Probability to apply crossover on every pair of individuals.
        mutpb (float): Probability to apply mutation on every individual.

    Yields:
        self

    Attributes:
        population: The population updated every generation.
        nevals: The number of evaluations in the last generation.
        toolbox
        selection_type
        lambda_
        cxpb
        mutpb

    Examples:
        This algorithm can continue the optimization indefinetely util stopped.
        Each iteration it yields itself to give access to its internal parameters.
        It can be used as follow::

            for state in MuLambdaAlgorithm(pop, toolbox, "+", 50, CXPB, MUTPB):
                if min(state.population, key=lambda ind: ind.fitness.values) < 1e-6:
                    break

        Any attribute can be changed during evolution. For example, to change the
        population, directly use the state ::

            for state in MuLambdaAlgorithm(pop, toolbox, "+", 50, CXPB, MUTPB):
                state.population = new_population()

    """
    def __init__(self, population, toolbox, selection_type, lambda_, cxpb, mutpb):
        self.population = population
        self.toolbox = toolbox
        self.selection_type = selection_type
        self.lambda_ = lambda_
        self.cxpb = cxpb
        self.mutpb = mutpb
        self.nevals = 0

        assert selection_type in {"plus", "comma", "+", ","}, (
            "Selection type {} not in {'plus', 'comma'}, "
        ).format(selection_type)

    def __iter__(self):
        return self

    def next(self):
        # Vary the population
        offspring = take(
            self.lambda_,
            or_variation(self.population, self.toolbox, self.cxpb, self.mutpb)
        )

        # Evaluate the new individuals
        self.nevals = evaluate_invalids(offspring, self.toolbox.evaluate, self.toolbox.map)

        if self.selection_type in {"plus", "+"}:
            offspring = self.population + offspring

        # Select the next generation population
        self.population = self.toolbox.select(offspring, len(self.population))

        return self


class GenerateUpdateAlgorithm:
    """Two step evolutionary algorithm -- generate/update.

    Each iteration, individuals are produced using the toolbox's generate method.
    These individuals are evaluted and passed to the toolbox's update method.

    Args:
        toolbox (deap.base.Toolbox): Toolbox containing the *generate* and
            *update* methods.

    Yields:
        self

    Attributes:
        population: The population updated every generation.
        nevals: The number of evaluations in the last generation.
        toolbox

    Examples:
        This algorithm can continue the optimization indefinetely util stopped.
        Each iteration it yields itself to give access to its internal parameters.
        It can be used as follow::

            for state in GenerateUpdateAlgorithm(toolbox):
                if min(state.population, key=lambda ind: ind.fitness.values) < 1e-6:
                    break

        Any attribute can be changed during evolution. For example, to change the
        generation method at some point in the evolution, use the state ::

            for g, state in enumerate(GenerateUpdateAlgorithm(toolbox)):
                if g > 50:
                    state.toolbox = new_toolbox()

    """
    def __init__(self, toolbox):
        self.toolbox = toolbox
        self.population = None
        self.nevals = 0

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        # Generate a new population
        self.population = self.toolbox.generate()

        # Evaluate the new individuals
        self.nevals = evaluate_invalids(self.population, self.toolbox.evaluate,
                                        self.toolbox.map)

        # Update the strategy with the evaluated individuals
        self.toolbox.update(self.population)

        return self
