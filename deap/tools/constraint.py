
from functools import wraps

class Penality(object):
    """Contraint decorator for evaluation function. This decorator requires
    a *feasibility* function that returns :data:`True` for a valid *individual*
    and :data:`False` otherwise. The *delta* parameter is a constant value
    added as offset to the optional *distance* function. The distance
    function shall return a value growing as the individual moves away
    the valid zone.

    :param feasibility: A function returning the validity status of any
                        individual
    :param delta: Constant returned for an invalid individual.
    :param distance: Distance between the individual and a given valid point.
    :returns: A decorator for evaluation function.

    See the :doc:`/tutorials/advanced/constraints` for an example.
    """
    def __init__(self, feasibility, delta, distance=None):
        self.fbty_fct = feasibility
        self.delta = delta
        self.dist_fct = distance

    def __call__(self, func):
        @wraps(func)
        def wrapper(individual, *args, **kwargs):
            if self.fbty_fct(individual):
                return func(individual, *args, **kwargs)

            dist = 0
            if self.dist_fct is not None:
                dist = self.dist_fct(individual)
            return self.delta + dist,

        return wrapper

class ClosestPenality(object):
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
            f_fbl = func(f_ind, *args, **kwargs)

            dist = 0
            if self.dist_fct is not None:
                dist = self.dist_fct(f_ind, individual)
            
            return tuple(f + self.alpha * dist for f in f_fbl)

        return wrapper

# List of exported function names.
__all__ = ['Penality', 'ClosestPenality']

if __name__ == "__main__":
    def feasible(individual):
        """A user defined function that returns :data:`True` for
        a valid *individual* and :data:`False` otherwise.
        """
        if individual[0] > 1.0:
            return False
        return True

    @Penality(feasible, 100, lambda ind: ind[0]**2)
    def evaluate(individual):
        """A standard evaluation function decorated with the
        :class:`Penality` decorator, for which *delta* is set to
        100 and the distance is set quadratic on the first variable.
        """
        return sum(individual),

    ind1 = [0.5, 1.0, 1.0, 1.0]
    print evaluate(ind1)

    ind2 = [3.0, 1.0, 1.0, 1.0]
    print evaluate(ind2)
