"""The :mod:`~deap.base` module provides basic structures to build
evolutionary algorithms. It contains the :class:`~deap.base.Toolbox`, useful
to store evolutionary operators, and a virtual :class:`~deap.base.Fitness`
class used as base class, for the fitness member of any individual. """

from functools import partial
from operator import mul, truediv

from collections.abc import Callable, Sequence
from copy import deepcopy
from functools import wraps
from operator import attrgetter
from typing import Any, Callable, Collection, List, Tuple

import numpy


class Fitness:
    """Class for initializing fitnesses in an individual.

    The fitness is a measure of quality of a solution. If *initval* is
    provided as a single value or a tuple, the fitness is initalized using
    those values, otherwise it is empty (or invalid). The values are converted
    to numpy.float64 when set, ensure your values can be safely casted using
    ``numpy.asarray(value, dtype=numpy.float64)``.

    Fitnesses may be compared using the ``>``, ``<``, ``>=``, ``<=``, ``==``,
    ``!=``. The comparisons are made through a strict dominance criteria meaning
    that two fitnesses are considered equal if neither dominates the other.

    Constraint handling can be provided. A fitness violating a constraint (invalid)
    will always be dominated by a valid fitness. Two invalid fitnesses compare
    as if they were valid.

    Arguments:
        objectives (scalar or sequence): Usualy one of :data:`Fitness.MAXIMIZE`
            or :data:`Fitness.MINIMIZE` or a tuple thereof.
        initval (scalar or sequence): Initial value for a fitness. When not provided
            the fitness remains invalid until its value is set.
        violated_constraints (sequence of boolean): A list of booleans which assess if
            if a constraint is violated.


    Examples:
        Fitnesses can be compared directly::

            >>> obj = Fitness.MAXIMIZE
            >>> f1 = Fitness(obj, initval=2)
            >>> f2 = Fitness(obj, initval=3)

            >>> f1 > f2
            False
            >>> f1 < f2
            True

        Multiobjective fitnesses compare using strict domimance::

            >>> mobj = (Fitness.MAXIMIZE, Fitness.MAXIMIZE)
            >>> f1 = Fitness(mobj, initval=(2, 3))
            >>> f2 = Fitness(mobj, initval=(2, 4))

            >>> f1 < f2
            True
            >>> f1 > f2
            False

        Strict dominance imply that all objective must be atleast be better
        or equal for one fitness to dominate the other. In this example neither
        fitness dominates the other::

            >>> mobj = (Fitness.MAXIMIZE, Fitness.MAXIMIZE)
            >>> f1 = Fitness(mobj, initval=(2, 3))
            >>> f2 = Fitness(mobj, initval=(1, 4))

            >>> f1 < f2
            False
            >>> f1 > f2
            False
            >>> f1 == f2
            True

        Constraint handling can be done inside fitnesses::

            >>> f1 = Fitness(Fitness.MAXIMIZE,
            ...              initval=11,
            ...              violated_constraints=[True, False])
            >>> f1.valid
            False

            >>> f2 = Fitness(Fitness.MAXIMIZE,
            ...              initval=5,
            ...              violated_constraints=[False, False])
            >>> f2.valid
            True

            >>> f2 > f1
            True


    """
    MAXIMIZE = 1.0
    MINIMIZE = -1.0

    def __init__(self, objectives, initval=(), violated_constraints=()):
        if not isinstance(objectives, Sequence):
            objectives = (objectives,)

        self.objectives = numpy.asarray(objectives, dtype=numpy.float64)
        self._value: numpy.ndarray = numpy.asarray((), dtype=numpy.float64)
        self._wvalue: numpy.ndarray = numpy.array((), dtype=numpy.float64)
        self._violated_constraints = violated_constraints

        self.value = initval

    def _getvalue(self) -> numpy.ndarray:
        """Raw values of this fitness as numpy.array of type float64."""
        return self._value

    def _setvalue(self, val):
        if val is None:
            val = ()

        if isinstance(val, str) \
                or (not isinstance(val, Sequence)
                    and not isinstance(val, numpy.ndarray)):
            val = (val,)

        if len(val) > 0 and len(val) != len(self.objectives):
            raise ValueError(f"setting fitness with {len(val)} "
                             f"value{'s' if len(val) > 1 else ''}, "
                             f"{len(self.objectives)} expected.")

        self._value = numpy.asarray(val, dtype=numpy.float64)

        if len(val) > 0:
            # Store objective relative values for performance
            self._wvalue = self._value * self.objectives

    def _delvalue(self):
        self._value = numpy.asarray((), dtype=numpy.float64)

    value = property(_getvalue, _setvalue, _delvalue)

    @property
    def violated_constraints(self):
        """Status of constraint violations for this fitness."""
        return self._violated_constraints

    @violated_constraints.setter
    def violated_constraints(self, violated_constraints):
        self._violated_constraints = violated_constraints

    @violated_constraints.deleter
    def violated_constraints(self):
        self._violated_constraints = ()

    def reset(self):
        """Reset the values and constraint violations of this fitness."""
        del self.value
        del self.violated_constraints

    @property
    def valid(self):
        """Assess if a fitness is valid or not. Either the fitness never
        received a value or it violates one or more constraints."""
        return self.evaluated and not any(self.violated_constraints)

    @property
    def evaluated(self):
        """Assess if a fitness received a value."""
        return self._value.size > 0

    def __lt__(self, other: "Fitness") -> bool:
        return other._dominates(self)

    def __le__(self, other: "Fitness") -> bool:
        return self < other or self == other

    def __eq__(self, other: "Fitness") -> bool:
        return not self._dominates(other) and not other._dominates(self)

    def __ge__(self, other: "Fitness") -> bool:
        return not self < other

    def __gt__(self, other: "Fitness") -> bool:
        return not self <= other

    def _dominates(self, other: "Fitness") -> bool:
        if not self.evaluated or not other.evaluated:
            raise ValueError("Cannot compare fitnesses without values in"
                             f", {self} dominates {other}")

        self_valid = self.valid
        other_valid = other.valid

        if self_valid and not other_valid:
            return True
        elif not self_valid and other_valid:
            return False

        if numpy.any(self._wvalue < other._wvalue):
            return False
        if numpy.any(self._wvalue > other._wvalue):
            return True
        return False

    def __str__(self):
        return str(self._value)


class Attribute:
    """General attribute in an :class:`Individual`.

    Attribute are placeholders in an :class:`Individual`. Individuals will initialize
    attribute as properties allowing to set and get their values properly.

    Arguments:
        initval (any): Initial value for the attribute. Can be of any type.

    """
    def __init__(self, initval: Any = None):
        self.value = initval

    def _getvalue(self) -> None:
        return self.value

    def _setvalue(self, val: Any) -> None:
        self.value = val

    def _delvalue(self) -> None:
        self.value = None

    def __str__(self) -> str:
        return str(self.value)


class Individual:
    """Base class for individuals.

    Abstract base class for individuals. This class turns fitness and attribute
    members into property like objects that can be set directly with their values.

    The individual is a mix of attribute and fitnesses. An individuals can have as
    many attribute and fitnesses as desired. However, when having multiple attribute
    or fitnesses the key argument in variations and/or selections becomes mandatory.

    Note:
        Predefined algorithms are not capable of handling multiple fitnesses.

    Examples:

        An individual with a single array of attribute and a single fitness.

            >>> from operator import attrgetter
            >>> import numpy

            >>> class AwesomeIndividual(Individual):
            ...     def __init__(self, alpha, beta, size):
            ...         super().__init__()
            ...         self.fitness = Fitness(Fitness.MINIMIZE)
            ...         values = numpy.random.beta(alpha, beta, size)
            ...         self.attrs = Attribute(values)

            >>> i1 = AwesomeIndividual(alpha=1, beta=2, size=5)
            >>> i2 = AwesomeIndividual(alpha=1, beta=2, size=5)
            >>> i1.fitness = 2
            >>> i2.fitness = 5
            >>> ordered = sorted([i1, i2], key=attrgetter("fitness"))
            >>> ordered == [i2, i1]
            True

        An individual with two arrays of attribute and a single fitness.

            >>> from operator import attrgetter
            >>> import numpy

            >>> class AwesomeIndividual(Individual):
            ...     def __init__(self, alpha, beta, lam, fsize, isize):
            ...         super().__init__()
            ...         self.fitness = Fitness(Fitness.MINIMIZE)
            ...         val_float = numpy.random.beta(alpha, beta, fsize)
            ...         self.attrs_float = Attribute(val_float)
            ...         val_int = numpy.random.poisson(lam, isize)
            ...         self.attrs_int = Attribute(val_int)

            >>> i1 = AwesomeIndividual(alpha=1, beta=2, lam=5, fsize=5, isize=10)

        An individual with a single array of attribute and two fitnesses.

            >>> from operator import attrgetter
            >>> import numpy

            >>> class AwesomeIndividual(Individual):
            ...     def __init__(self, alpha, beta, size):
            ...         super().__init__()
            ...         self.fitness_a = Fitness(Fitness.MINIMIZE)
            ...         self.fitness_b = Fitness((Fitness.MINIMIZE, Fitness.MAXIMIZE))
            ...         val_float = numpy.random.beta(alpha, beta, size)
            ...         self.attrs_float = Attribute(val_float)

            >>> i1 = AwesomeIndividual(alpha=1, beta=2, size=5)
            >>> i1.fitness_a = 2
            >>> i1.fitness_b = (5, 3)

    """
    def __init__(self):
        self._fitnesses = dict()
        self._attribute = dict()

    def _register_fitness(self, name, fitness):
        self._fitnesses[name] = fitness

    def _register_attribute(self, name, attribute):
        self._attribute[name] = attribute

    def _register_property(self, name, type_):
        def _getter(self):
            # Return the object and not the values to be able to use them
            # with all their instance methods (i.e., return a Fitness not a ndarray)
            return self.__getattribute__(type_)[name]

        def _setter(self, val):
            self.__getattribute__(type_)[name]._setvalue(val)

        def _deletter(self):
            self.__getattribute__(type_)[name]._delvalue()

        # Property is a class attribute
        setattr(Individual, name, property(_getter, _setter, _deletter))

    def _getattribute(self, name=None):
        """Retrieve the attribute of this individual. If *name* is provided, retrieve
        the attribute with name *name*. Name is mandatory for individuals having
        more than one attribute.

        Note:
            This method is generally for internal use.
        """
        if name is None and len(self._attribute) == 1:
            name = next(iter(self._attribute.keys()))
        elif name is None:
            raise AttributeError("individual with multiple attribute "
                                 "require the 'name' argument in operators")
        return getattr(self, name)

    def _setattribute(self, name=None, value=None):
        """Set the attribute of this individual. If *name* is provided, set
        the attribute with name *name*. Name is mandatory for individuals having
        more than one attribute.

        Note:
            This method is generally for internal use.
        """
        if name is None and len(self._attribute) == 1:
            name = next(iter(self._attribute.keys()))
        elif name is None:
            raise AttributeError("individual with multiple attribute "
                                 "require the 'name' argument in operators")
        return setattr(self, name, value)

    def _getfitness(self, name=None):
        """Retrieve the fitness of this individual. If *name* is provided, retrieve
        the fitness with name *name*. Name is mandatory for individuals having
        more than one fitness.

        Note:
            This method is generally for internal use.
        """
        if name is None and len(self._fitnesses) == 1:
            name = next(iter(self._fitnesses.keys()))
        elif name is None:
            raise AttributeError("individual with multiple fitnesses "
                                 "require the 'name' argument in operators")
        return getattr(self, name)

    def _setfitness(self, name=None, value=None):
        """Set the fitness of this individual. If *name* is provided, set
        the fitness with name *name*. Name is mandatory for individuals having
        more than one fitness.

        Note:
            This method is generally for internal use.
        """
        if name is None and len(self._fitnesses) == 1:
            name = next(iter(self._fitnesses.keys()))
        elif name is None:
            raise AttributeError("individual with multiple fitnesses "
                                 "require the 'name' argument in operators")
        return setattr(self, name, value)

    def invalidate_fitness(self):
        """Invalidate all fitnesses of this individual.

        Note:
            This method is generally for internal use.
        """
        for f in self._fitnesses.values():
            f.reset()

    def __setattr__(self, name, value):
        if isinstance(value, Fitness):
            if getattr(self, "_fitnesses", None) is None:
                self._fitnesses = dict()

            self._register_fitness(name, value)
            self._register_property(name, "_fitnesses")

        elif isinstance(value, Attribute):
            if getattr(self, "_attribute", None) is None:
                self._attribute = dict()

            self._register_attribute(name, value)
            self._register_property(name, "_attribute")

        else:
            super().__setattr__(name, value)

    def __str__(self):
        str_values = ', '.join('='.join((name, str(attr.getvalue())))
                               for name, attr in self._attribute.items())
        return f"{self.__class__.__name__}({str_values})"


class Toolbox(object):
    """A toolbox for the evolutionary operators. At
    first the toolbox contains a :meth:`~deap.toolbox.clone` method that
    duplicates any element it is passed as argument, this method defaults to
    the :func:`copy.deepcopy` function. and a :meth:`~deap.toolbox.map`
    method that applies the function given as first argument to every items
    of the iterables given as next arguments, this method defaults to the
    :func:`map` function. You may populate the toolbox with any other
    function by using the :meth:`~deap.base.Toolbox.register` method.

    Concrete usages of the toolbox are shown for initialization in the
    :ref:`creating-types` tutorial and for tools container in the
    :ref:`next-step` tutorial.
    """

    def __init__(self):
        self.register("map", map)

    def register(self, alias, function, *args, **kargs):
        """Register a *function* in the toolbox under the name *alias*. You
        may provide default arguments that will be passed automatically when
        calling the registered function. Fixed arguments can then be overriden
        at function call time.

        :param alias: The name the operator will take in the toolbox. If the
                      alias already exist it will overwrite the the operator
                      already present.
        :param function: The function to which refer the alias.
        :param argument: One or more argument (and keyword argument) to pass
                         automatically to the registered function when called,
                         optional.

        The following code block is an example of how the toolbox is used. ::

            >>> def func(a, b, c=3):
            ...     print(a, b, c)
            ...
            >>> tools = Toolbox()
            >>> tools.register("myFunc", func, 2, c=4)
            >>> tools.myFunc(3)
            2 3 4

        The registered function will be given the attribute :attr:`__name__`
        set to the alias and :attr:`__doc__` set to the original function's
        documentation. The :attr:`__dict__` attribute will also be updated
        with the original function's instance dictionary, if any.
        """
        pfunc = partial(function, *args, **kargs)
        pfunc.__name__ = alias
        pfunc.__doc__ = function.__doc__

        if hasattr(function, "__dict__") and not isinstance(function, type):
            # Some functions don't have a dictionary, in these cases
            # simply don't copy it. Moreover, if the function is actually
            # a class, we do not want to copy the dictionary.
            pfunc.__dict__.update(function.__dict__.copy())

        setattr(self, alias, pfunc)

    def unregister(self, alias):
        """Unregister *alias* from the toolbox.

        :param alias: The name of the operator to remove from the toolbox.
        """
        delattr(self, alias)

    def decorate(self, alias, *decorators):
        """Decorate *alias* with the specified *decorators*, *alias*
        has to be a registered function in the current toolbox.

        :param alias: The name of the operator to decorate.
        :param decorator: One or more function decorator. If multiple
                          decorators are provided they will be applied in
                          order, with the last decorator decorating all the
                          others.

        .. note::
            Decorate a function using the toolbox makes it unpicklable, and
            will produce an error on pickling. Although this limitation is not
            relevant in most cases, it may have an impact on distributed
            environments like multiprocessing.
            A function can still be decorated manually before it is added to
            the toolbox (using the @ notation) in order to be picklable.
        """
        pfunc = getattr(self, alias)
        function, args, kargs = pfunc.func, pfunc.args, pfunc.keywords
        for decorator in decorators:
            function = decorator(function)
        self.register(alias, function, *args, **kargs)
