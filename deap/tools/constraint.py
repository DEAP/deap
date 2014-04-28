
from functools import wraps
from itertools import repeat
from collections import Sequence

class DeltaPenality(object):
    """This decorator returns penalized fitness for invalid individuals and the
    original fitness value for valid individuals. The penalized fitness is made
    of a constant factor *delta* added with an (optional) *distance* penality. The
    distance function, if provided, shall return a value growing as the
    individual moves away the valid zone.

    :param feasibility: A function returning the validity status of any
                        individual.
    :param delta: Constant or array of constants returned for an invalid individual.
    :param distance: A function returning the distance between the individual
                     and a given valid point (optional, defaults to 0).
    :returns: A decorator for evaluation function.

    This function relies on the fitness weights to add correctly the distance.
    The fitness value of the ith objective is defined as

    .. math::

       f^\mathrm{penality}_i(\mathbf{x}) = \Delta_i - w_i d(\mathbf{x})

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

            dist = 0
            if self.dist_fct is not None:
                dist = self.dist_fct(individual)
            return tuple(d - w * dist for d, w in zip(self.delta, weights))

        return wrapper

class ClosestValidPenality(object):
    """This decorator returns penalized fitness for invalid individuals and the
    original fitness value for valid individuals. The penalized fitness is made
    of the fitness of the closest valid individual added with a weighted
    (optional) *distance* penality. The distance function, if provided, shall
    return a value growing as the individual moves away the valid zone.

    :param feasibility: A function returning the validity status of any
                        individual.
    :param feasible: A function returning the closest feasible individual
                     from the current invalid individual.
    :param alpha: Multiplication factor on the distance between the valid and
                  invalid individual.
    :param distance: A function returning the distance between the individual
                     and a given valid point (optional, defaults to 0).
    :returns: A decorator for evaluation function.

    This function relies on the fitness weights to add correctly the distance.
    The fitness value of the ith objective is defined as

    .. math::

       f^\mathrm{penality}_i(\mathbf{x}) = f_i(\operatorname{valid}(\mathbf{x})) - \\alpha w_i d(\operatorname{valid}(\mathbf{x}), \mathbf{x})

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

            dist = 0
            if self.dist_fct is not None:
                dist = self.dist_fct(f_ind, individual)
            
            # print("returned", tuple(f - w * self.alpha * dist for f, w in zip(f_fbl, weights)))
            return tuple(f - w * self.alpha * dist for f, w in zip(f_fbl, weights))

        return wrapper

# List of exported function names.
__all__ = ['DeltaPenality', 'ClosestValidPenality']

if __name__ == "__main__":
    def feasible(individual):
        """A user defined function that returns :data:`True` for
        a valid *individual* and :data:`False` otherwise.
        """
        if individual[0] > 1.0:
            return False
        return True

    @DeltaPenality(feasible, 100, lambda ind: ind[0]**2)
    def evaluate(individual):
        """A standard evaluation function decorated with the
        :class:`DeltaPenality` decorator, for which *delta* is set to
        100 and the distance is set quadratic on the first variable.
        """
        return sum(individual),

    ind1 = [0.5, 1.0, 1.0, 1.0]
    print evaluate(ind1)

    ind2 = [3.0, 1.0, 1.0, 1.0]
    print evaluate(ind2)
