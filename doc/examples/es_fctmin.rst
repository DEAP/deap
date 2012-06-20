===========================
Evolution Strategies Basics
===========================

Evolution strategies are special types of evolutionary computation algorithms
where the mutation strength is learnt during the evolution. A first type of
strategy (endogenous) includes directly the mutation strength for each
attribute of an individual inside the individual. This mutation strength is
subject to evolution similarly to the individual in a classic genetic
algorithm. For more details, [Beyer2002]_ presents a very good introduction to
evolution strategies.

In order to have this kind of evolution we'll need a type of individual that
contains a :attr:`strategy` attribute. We'll also minimize the objective
function, which gives the following classes creation.

.. literalinclude:: /code/examples/es/es_fctmin.py
   :lines: 31-33

The initialization function for an evolution strategy is not defined by DEAP.
The following generation function takes as argument the class of individual
to instantiate, *icls*. It also takes the class of strategy to use as
strategy, *scls*. The next arguments are the minimum and maximum values for
the individual and strategy attributes. The strategy is added in the
:attr:`strategy` member of the returned individual.

.. literalinclude:: /code/examples/es/es_fctmin.py
   :pyobject: generateES

This generation function is registered in the toolbox like any other
initializer.

.. literalinclude:: /code/examples/es/es_fctmin.py
   :lines: 54-55

The strategy controls the standard deviation of the mutation. It is common to
have a lower bound on the values so that the algorithm don't fall in
exploitation only. This lower bound is added to the variation operator by
the following decorator.

.. literalinclude:: /code/examples/es/es_fctmin.py
   :pyobject: checkStrategy

The variation operators are decorated via the
:meth:`~deap.base.Toolbox.decorate` method of the toolbox and the evaluation
function is taken from the :mod:`~deap.benchmarks` module.

.. literalinclude:: /code/examples/es/es_fctmin.py
   :lines: 62-63,61,60

From here, everything left to do is either write the algorithm or use one
provided in :mod:`~deap.algorithms`. Here we will use the 
:func:`~deap.algorithms.eaMuCommaLambda` algorithm.

.. literalinclude:: /code/examples/es/es_fctmin.py
   :lines: 65,67-80

The complete example : [`source code <code/es/es_fctmin.py>`_].

.. [Beyer2002] Beyer and Schwefel, 2002, Evolution strategies - A Comprehensive Introduction
