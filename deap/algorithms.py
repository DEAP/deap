from copy import deepcopy
from itertools import cycle, islice, izip
import random


def evaluate_invalids(individuals, eval_func, map=map):
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
        ind.fitness.values = fit

    return len(invalid_ind)


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
        toolbox (base.Toolbox): The toolbox containing the crossover, mutation
            and mapping function to use for evolution.
        cxpb (float): Probability to apply crossover on every pair of individuals.
        mutpb (float): Probability to apply mutation on every individual.

    Yields:
        individual: Offspring produced by the variation.

    Example:
        The variation can generates new offspring indefinitely if required.
        To generate a given number of individual we :func:`~itertools.islice`
        this generator to the given amount::

            >>> offspring = list(islice(
            ...     and_variation(population, toolbox, 0.6, 0.3),
            ...     50
            ... ))

    """
    individuals = cycle(population)

    # zip(iter, iter) produces l[i], l[i+1]
    for i1, i2 in izip(individuals, individuals):
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
    deepcopies them before applying the operator and yields the result. In case
    of a crossover, only the first offspring is yielded to keep the number of
    individuals produced by crossover, mutation and copy proportional to the input
    probabilities. *cxpb* and *mutpb* shoudn't sum above 1.

    Args:
        population (iterable): The individuals to vary.
        toolbox (base.Toolbox): The toolbox containing the crossover, mutation
            and mapping function to use for evolution.
        cxpb (float): Probability to apply crossover on every pair of individuals.
        mutpb (float): Probability to apply mutation on every individual.

    Yields:
        individual: Offspring produced by the variation.

    Example:
        The variation can generates new offspring indefinitely if required.
        To generate a given number of individual, say 50, we
        :func:`~itertools.islice` this generator to the given amount::

            >>> offspring = list(islice(
            ...     or_variation(population, toolbox, 0.6, 0.3),
            ...     50
            ... ))

    """
    assert (cxpb + mutpb) <= 1.0, (
        "The sum of the crossover and mutation probabilities must be smaller "
        "or equal to 1.0."
    )

    while True:
        op_choice = random.random()
        if op_choice < cxpb:  # Apply crossover
            i1, i2 = random.sample(population, 2)
            # Must deepcopy separately to ensure full deepcopy if the same
            # individual is selected twice, it is deepcopied twice (what is
            # not true with deepcopy([i1, i2])).
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


class GenerationalAlgorithm:
    """Algorithm based on a generational process.

    Each iteration, the parental population is selected from the population
    for reproduction. It is advised to use a selection with replacement as
    N individuals will be selected from a population of size N. The parents
    get to reproduce using the :func:`and_variation`.

    Args:
        population (list): Initial population for the evolution.
        toolbox (deap.base.Toolbox):
        cxpb (float):
        mutpb (float):

    Yields:
        self

    Attributes:
        population (list): The generation updated every generation.
        toolbox (deap.base.Toolbox): The toolbox used during the evolution.
        cxpb (float):
        mutpb (float):
        nevals (int): The number of evaluations in the last generation.

    Examples:
        This algorithm can continue the optimization indefinetely or util stopped.
        Each iteration it yields itself to give access to its internal parameters.
        It can be used as follow::

            for state in GenerationAlgorithm(pop, toolbox, CXPB, MUTPB):
                if min(state.population, key=lambda ind: ind.fitness.values) < 1e-6:
                    break

        Any attribute can be changed during evolution. For example, to change the
        generation directly use the state ::

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
            "Selection type {} not in {'plus', 'comma'}, "
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
