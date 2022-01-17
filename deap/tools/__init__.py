"""The :mod:`~deap.tools` module contains the operators for evolutionary
algorithms. They are used to modify, select and move the individuals in their
environment. The set of operators it contains are readily usable in the
:class:`~deap.base.Toolbox`. In addition to the basic operators this module
also contains utility tools to enhance the basic algorithms with
:class:`Statistics`, :class:`HallOfFame`, and :class:`History`.
"""

from copy import deepcopy
from functools import wraps
from typing import Callable, List

from .constraint import *
from .crossover import *
from .emo import *
from .indicator import *
from .init import *
from .migration import *
from .mutation import *
from .selection import *
from .support import *

from ..base import Individual


def variation(func: Callable):
    """Decorator for variation functions. With this decorator, variations
    (crossovers and mutations) can be implemented as if they received attributes
    directly without regards to the attribute name inside the individual. The
    returned individuals are deepcopies of the original individuals with their
    attributes changed to the values returned by the variation. It is assumed
    the new attributes are different from the old ones and thus, the fitness is
    invalidated for each individual that received new attributes.

    Arguments:
        func (callable): A function operating on attributes of an individual.

    Returns:
        (callable): The decorated variation operator.

    Note:
        The callable shall return at most *n* new attributes, where *n* is the
        number of input attributes.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        key = kwargs.pop("key", None)
        individuals: List[Individual] = list()
        variator_args = list()
        variator_kwargs = dict()

        # Deepcopy passed individuals
        for argument in args:
            if isinstance(argument, Individual):
                copy_ = deepcopy(argument)
                individuals.append(copy_)
                argument = copy_._getattribute(key)

            variator_args.append(argument)

        # Deepcopy passed individuals
        for keyword, argument in kwargs.items():
            if isinstance(argument, Individual):
                copy_ = deepcopy(argument)
                individuals.append(copy_)
                argument = copy_._getattribute(key)

            variator_kwargs[keyword] = argument

        # Get variated attributes
        attributes = func(*variator_args, **variator_kwargs)

        # Replace the attributes by the variated attribues inside each
        # individual
        if len(individuals) > 1:
            for i, a in zip(individuals, attributes):
                i._setattribute(key, a)
                i.invalidate_fitness()

        else:
            individuals = individuals[0]
            individuals._setattribute(key, attributes)
            individuals.invalidate_fitness()

        # Return the whole individuals with their fitness invalidated
        return individuals

    return wrapper


def evaluation(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = kwargs.pop("key", None)
        evaluation_args = list()
        evaluation_kwargs = dict()

        # Deepcopy passed individuals
        for argument in args:
            if isinstance(argument, Individual):
                argument = argument._getattribute(key)

            evaluation_args.append(argument)

        # Deepcopy passed individuals
        for keyword, argument in kwargs.items():
            if isinstance(argument, Individual):
                argument = argument._getattribute(key)

            evaluation_kwargs[keyword] = argument

        # Get variated attributes
        fitness = func(*evaluation_args, **evaluation_kwargs)

        return fitness

    return wrapper
