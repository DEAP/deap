
from functools import wraps
from itertools import repeat
from collections import Sequence

class DeltaPenalty(object):
    """This decorator returns penalized fitness for invalid individuals and the
    original fitness value for valid individuals. The penalized fitness is made
    of a constant factor *delta* added with an (optional) *distance* penalty. The
    distance function, if provided, shall return a value growing as the
    individual moves away the valid zone.

    :param feasibility: A function returning the validity status of any
                        individual.
    :param delta: Constant or array of constants returned for an invalid individual.
    :param distance: A function returning the distance between the individual
                     and a given valid point. The distance function can also return a sequence
                     of length equal to the number of objectives to affect multi-objective
                     fitnesses differently (optional, defaults to 0).
    :returns: A decorator for evaluation function.

    This function relies on the fitness weights to add correctly the distance.
    The fitness value of the ith objective is defined as

    .. math::

       f^\mathrm{penalty}_i(\mathbf{x}) = \Delta_i - w_i d_i(\mathbf{x})

    where :math:`\mathbf{x}` is the individual, :math:`\Delta_i` is a user defined
    constant and :math:`w_i` is the weight of the ith objective. :math:`\Delta`
    should be worst than the fitness of any possible individual, this means
    higher than any fitness for minimization and lower than any fitness for
    maximization.

    See the :doc:`/tutorials/advanced/constraints` for an example.
    """
    def __init__(self, feasibility, delta, distance=None):
        self.fbty_fct = feasibility
        if not isinstance(delta, Sequence):
            self.delta = repeat(delta)
        else:
            self.delta = delta
        self.dist_fct = distance

    def __call__(self, func):
        @wraps(func)
        def wrapper(individual, *args, **kwargs):
            if self.fbty_fct(individual):
                return func(individual, *args, **kwargs)

            weights = tuple(1 if w >= 0 else -1 for w in individual.fitness.weights)

            dists = tuple(0 for w in individual.fitness.weights)
            if self.dist_fct is not None:
                dists = self.dist_fct(individual)
                if not isinstance(dists, Sequence):
                    dists = repeat(dists)
            return tuple(d - w * dist for d, w, dist in zip(self.delta, weights, dists))

        return wrapper

DeltaPenality = DeltaPenalty

class ClosestValidPenalty(object):
    """This decorator returns penalized fitness for invalid individuals and the
    original fitness value for valid individuals. The penalized fitness is made
    of the fitness of the closest valid individual added with a weighted
    (optional) *distance* penalty. The distance function, if provided, shall
    return a value growing as the individual moves away the valid zone.

    :param feasibility: A function returning the validity status of any
                        individual.
    :param feasible: A function returning the closest feasible individual
                     from the current invalid individual.
    :param alpha: Multiplication factor on the distance between the valid and
                  invalid individual.
    :param distance: A function returning the distance between the individual
                     and a given valid point. The distance function can also return a sequence
                     of length equal to the number of objectives to affect multi-objective
                     fitnesses differently (optional, defaults to 0).
    :returns: A decorator for evaluation function.

    This function relies on the fitness weights to add correctly the distance.
    The fitness value of the ith objective is defined as

    .. math::

       f^\mathrm{penalty}_i(\mathbf{x}) = f_i(\operatorname{valid}(\mathbf{x})) - \\alpha w_i d_i(\operatorname{valid}(\mathbf{x}), \mathbf{x})

    where :math:`\mathbf{x}` is the individual,
    :math:`\operatorname{valid}(\mathbf{x})` is a function returning the closest
    valid individual to :math:`\mathbf{x}`, :math:`\\alpha` is the distance
    multiplicative factor and :math:`w_i` is the weight of the ith objective.
    """

    def __init__(self, feasibility, feasible, alpha, distance=None):
        self.fbty_fct = feasibility
        self.fbl_fct = feasible
        self.alpha = alpha
        self.dist_fct = distance

    def __call__(self, func):
        @wraps(func)
        def wrapper(individual, *args, **kwargs):
            if self.fbty_fct(individual):
                return func(individual, *args, **kwargs)

            f_ind = self.fbl_fct(individual)
            # print("individual", f_ind)
            f_fbl = func(f_ind, *args, **kwargs)
            # print("feasible", f_fbl)

            weights = tuple(1.0 if w >= 0 else -1.0 for w in individual.fitness.weights)

            if len(weights) != len(f_fbl):
                raise IndexError("Fitness weights and computed fitness are of different size.")

            dists = tuple(0 for w in individual.fitness.weights)
            if self.dist_fct is not None:
                dist = self.dist_fct(f_ind, individual)
                if not isinstance(dists, Sequence):
                    dists = repeat(dists)

            # print("returned", tuple(f - w * self.alpha * dist for f, w in zip(f_fbl, weights)))
            return tuple(f - w * self.alpha * d for f, w, d in zip(f_fbl, weights, dists))

        return wrapper

ClosestValidPenality = ClosestValidPenalty

# List of exported function names.
__all__ = ['DeltaPenalty', 'ClosestValidPenalty', 'DeltaPenality', 'ClosestValidPenality']

if __name__ == "__main__":
    from deap import base
    from deap import benchmarks
    from deap import creator
    from deap import tools

    import numpy

    MIN_BOUND = numpy.array([0] * 30)
    MAX_BOUND = numpy.array([1] * 30)

    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    def distance(feasible_ind, original_ind):
        """A distance function to the feasibility region."""
        return sum((f - o)**2 for f, o in zip(feasible_ind, original_ind))

    def closest_feasible(individual):
        """A function returning a valid individual from an invalid one."""
        feasible_ind = numpy.array(individual)
        feasible_ind = numpy.maximum(MIN_BOUND, feasible_ind)
        feasible_ind = numpy.minimum(MAX_BOUND, feasible_ind)
        return feasible_ind

    def valid(individual):
        """Determines if the individual is valid or not."""
        if any(individual < MIN_BOUND) or any(individual > MAX_BOUND):
            return False
        return True

    toolbox = base.Toolbox()
    toolbox.register("evaluate", benchmarks.zdt2)
    toolbox.decorate("evaluate", ClosestValidPenalty(valid, closest_feasible, 1.0e-6, distance))

    ind1 = creator.Individual((-5.6468535666e-01,2.2483050478e+00,-1.1087909644e+00,-1.2710112861e-01,1.1682438733e+00,-1.3642007438e+00,-2.1916417835e-01,-5.9137308999e-01,-1.0870160336e+00,6.0515070232e-01,2.1532075914e+00,-2.6164718271e-01,1.5244071578e+00,-1.0324305612e+00,1.2858152343e+00,-1.2584683962e+00,1.2054392372e+00,-1.7429571973e+00,-1.3517256013e-01,-2.6493429355e+00,-1.3051320798e-01,2.2641961090e+00,-2.5027232340e+00,-1.2844874148e+00,1.9955852925e+00,-1.2942218834e+00,3.1340109155e+00,1.6440111097e+00,-1.7750105857e+00,7.7610242710e-01))
    print(toolbox.evaluate(ind1))
    print("Individuals is valid: %s" % ("True" if valid(ind1) else "False"))

