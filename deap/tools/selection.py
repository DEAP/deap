from __future__ import division
import random
import numpy as np

from functools import partial
from operator import attrgetter

######################################
# Selections                         #
######################################

def selRandom(individuals, k):
    """Select *k* individuals at random from the input *individuals* with
    replacement. The list returned contains references to the input
    *individuals*.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :returns: A list of selected individuals.

    This function uses the :func:`~random.choice` function from the
    python base :mod:`random` module.
    """
    return [random.choice(individuals) for i in xrange(k)]


def selBest(individuals, k, fit_attr="fitness"):
    """Select the *k* best individuals among the input *individuals*. The
    list returned contains references to the input *individuals*.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param fit_attr: The attribute of individuals to use as selection criterion
    :returns: A list containing the k best individuals.
    """
    return sorted(individuals, key=attrgetter(fit_attr), reverse=True)[:k]


def selWorst(individuals, k, fit_attr="fitness"):
    """Select the *k* worst individuals among the input *individuals*. The
    list returned contains references to the input *individuals*.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param fit_attr: The attribute of individuals to use as selection criterion
    :returns: A list containing the k worst individuals.
    """
    return sorted(individuals, key=attrgetter(fit_attr))[:k]


def selTournament(individuals, k, tournsize, fit_attr="fitness"):
    """Select the best individual among *tournsize* randomly chosen
    individuals, *k* times. The list returned contains
    references to the input *individuals*.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param tournsize: The number of individuals participating in each tournament.
    :param fit_attr: The attribute of individuals to use as selection criterion
    :returns: A list of selected individuals.

    This function uses the :func:`~random.choice` function from the python base
    :mod:`random` module.
    """
    chosen = []
    for i in xrange(k):
        aspirants = selRandom(individuals, tournsize)
        chosen.append(max(aspirants, key=attrgetter(fit_attr)))
    return chosen

def selRoulette(individuals, k, fit_attr="fitness"):
    """Select *k* individuals from the input *individuals* using *k*
    spins of a roulette. The selection is made by looking only at the first
    objective of each individual. The list returned contains references to
    the input *individuals*.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param fit_attr: The attribute of individuals to use as selection criterion
    :returns: A list of selected individuals.

    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.

    .. warning::
       The roulette selection by definition cannot be used for minimization
       or when the fitness can be smaller or equal to 0.
    """

    s_inds = sorted(individuals, key=attrgetter(fit_attr), reverse=True)
    sum_fits = sum(getattr(ind, fit_attr).values[0] for ind in individuals)
    chosen = []
    for i in xrange(k):
        u = random.random() * sum_fits
        sum_ = 0
        for ind in s_inds:
            sum_ += getattr(ind, fit_attr).values[0]
            if sum_ > u:
                chosen.append(ind)
                break

    return chosen


def selDoubleTournament(individuals, k, fitness_size, parsimony_size, fitness_first, fit_attr="fitness"):
    """Tournament selection which use the size of the individuals in order
    to discriminate good solutions. This kind of tournament is obviously
    useless with fixed-length representation, but has been shown to
    significantly reduce excessive growth of individuals, especially in GP,
    where it can be used as a bloat control technique (see
    [Luke2002fighting]_). This selection operator implements the double
    tournament technique presented in this paper.

    The core principle is to use a normal tournament selection, but using a
    special sample function to select aspirants, which is another tournament
    based on the size of the individuals. To ensure that the selection
    pressure is not too high, the size of the size tournament (the number
    of candidates evaluated) can be a real number between 1 and 2. In this
    case, the smaller individual among two will be selected with a probability
    *size_tourn_size*/2. For instance, if *size_tourn_size* is set to 1.4,
    then the smaller individual will have a 0.7 probability to be selected.

    .. note::
        In GP, it has been shown that this operator produces better results
        when it is combined with some kind of a depth limit.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param fitness_size: The number of individuals participating in each \
    fitness tournament
    :param parsimony_size: The number of individuals participating in each \
    size tournament. This value has to be a real number\
    in the range [1,2], see above for details.
    :param fitness_first: Set this to True if the first tournament done should \
    be the fitness one (i.e. the fitness tournament producing aspirants for \
    the size tournament). Setting it to False will behaves as the opposite \
    (size tournament feeding fitness tournaments with candidates). It has been \
    shown that this parameter does not have a significant effect in most cases\
    (see [Luke2002fighting]_).
    :param fit_attr: The attribute of individuals to use as selection criterion
    :returns: A list of selected individuals.

    .. [Luke2002fighting] Luke and Panait, 2002, Fighting bloat with
        nonparametric parsimony pressure
    """
    assert (1 <= parsimony_size <= 2), "Parsimony tournament size has to be in the range [1, 2]."

    def _sizeTournament(individuals, k, select):
        chosen = []
        for i in xrange(k):
            # Select two individuals from the population
            # The first individual has to be the shortest
            prob = parsimony_size / 2.
            ind1, ind2 = select(individuals, k=2)

            if len(ind1) > len(ind2):
                ind1, ind2 = ind2, ind1
            elif len(ind1) == len(ind2):
                # random selection in case of a tie
                prob = 0.5

            # Since size1 <= size2 then ind1 is selected
            # with a probability prob
            chosen.append(ind1 if random.random() < prob else ind2)

        return chosen

    def _fitTournament(individuals, k, select):
        chosen = []
        for i in xrange(k):
            aspirants = select(individuals, k=fitness_size)
            chosen.append(max(aspirants, key=attrgetter(fit_attr)))
        return chosen

    if fitness_first:
        tfit = partial(_fitTournament, select=selRandom)
        return _sizeTournament(individuals, k, tfit)
    else:
        tsize = partial(_sizeTournament, select=selRandom)
        return _fitTournament(individuals, k, tsize)

def selStochasticUniversalSampling(individuals, k, fit_attr="fitness"):
    """Select the *k* individuals among the input *individuals*.
    The selection is made by using a single random value to sample all of the
    individuals by choosing them at evenly spaced intervals. The list returned
    contains references to the input *individuals*.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param fit_attr: The attribute of individuals to use as selection criterion
    :return: A list of selected individuals.

    This function uses the :func:`~random.uniform` function from the python base
    :mod:`random` module.
    """
    s_inds = sorted(individuals, key=attrgetter(fit_attr), reverse=True)
    sum_fits = sum(getattr(ind, fit_attr).values[0] for ind in individuals)

    distance = sum_fits / float(k)
    start = random.uniform(0, distance)
    points = [start + i*distance for i in xrange(k)]

    chosen = []
    for p in points:
        i = 0
        sum_ = getattr(s_inds[i], fit_attr).values[0]
        while sum_ < p:
            i += 1
            sum_ += getattr(s_inds[i], fit_attr).values[0]
        chosen.append(s_inds[i])

    return chosen

def lexicasePreselection(individuals):
    """Preselects one individual per distinct error vector. This is crucial
    for avoiding the worst case runtime of lexicase selection but does not
    impact the behavior of which indiviudal gets selected."""

    unique_error_vectors = np.unique(
        [i.fitness.wvalues for i in individuals],
        axis=0)
    one_individual_per_err_vec = []
    for error_vec in unique_error_vectors:
        individuals_w_err_vec = [i for i in individuals if np.array_equal(i.fitness.wvalues, error_vec)]
        one_individual_per_err_vec.append(random.choice(individuals_w_err_vec))

    return one_individual_per_err_vec

def selLexicase(individuals, k):
    """Returns an individual that does the best on the fitness cases when
    considered one at a time in random order.
    http://faculty.hampshire.edu/lspector/pubs/lexicase-IEEE-TEC.pdf

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :returns: A list of selected individuals.
    """
    preselected_individuals = lexicasePreselection(individuals)
    selected_individuals = []

    for i in range(k):
        candidates = preselected_individuals
        cases = list(range(len(preselected_individuals[0].fitness.wvalues)))
        random.shuffle(cases)

        while len(cases) > 0 and len(candidates) > 1:
            best_val_for_case = max([indiv.fitness.wvalues[cases[0]] for indiv in candidates])
            candidates = [indiv for indiv in candidates if indiv.fitness.wvalues[cases[0]] == best_val_for_case]
            cases.pop(0)

        selected_individuals.append(random.choice(candidates))

    return selected_individuals

def selEpsilonLexicase(individuals, k, epsilon='dynamic'):
    """Returns an individual that does the best on the fitness cases when
    considered one at a time in random order. Requires a epsilon parameter.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param epsilon: If an individual is within epsilon of being elite, it will \
    remain in the selection pool. If 'dynamic', epsilon is set at the start of \
    each selection even. If 'super-dynamic', epsilon is set realtive to the \
    current selection pool at each iteration of lexicase selection.
    :returns: A list of selected individuals.
    """

    # Median Absolute Deviation
    def _mad(X):
        median = np.median(X)
        return np.median([abs(x - median) for x in X])

    preselected_individuals = lexicasePreselection(individuals)
    selected_individuals = []

    # If epsilon is dynamic, compute all values for epsilon ahead of time.
    epsilons = []
    if epsilon == 'dynamic':
        for i in list(range(len(preselected_individuals[0].fitness.wvalues))):
            ep = _mad([indiv.fitness.wvalues[i] for indiv in preselected_individuals])
            epsilons.append(ep)

    for i in range(k):
        candidates = preselected_individuals
        cases = list(range(len(preselected_individuals[0].fitness.wvalues)))
        random.shuffle(cases)

        while len(cases) > 0 and len(candidates) > 1:

            # Determing _epsilon for this iteration of lexicase.
            _epsilon = None
            if epsilon == 'super-dynamic':
                # Compute epsilon based on current pool.
                _epsilon = _mad([indiv.fitness.wvalues[cases[0]] for indiv in candidates])
            elif epsilon == 'dynamic':
                # Compute epsilon based on population.
                _epsilon = epsilons[cases[0]]
            else:
                # Epsilon must be passed as numeric from arguments.
                _epsilon = epsilon

            best_val_for_case = max([indiv.fitness.wvalues[cases[0]] for indiv in candidates])
            min_val_to_survive_case = best_val_for_case - _epsilon
            candidates = [indiv for indiv in candidates if indiv.fitness.wvalues[cases[0]] >= min_val_to_survive_case]
            cases.pop(0)

        selected_individuals.append(random.choice(candidates))

    return selected_individuals

__all__ = ['selRandom', 'selBest', 'selWorst', 'selRoulette',
           'selTournament', 'selDoubleTournament', 'selStochasticUniversalSampling',
           'selLexicase', 'selEpsilonLexicase']
