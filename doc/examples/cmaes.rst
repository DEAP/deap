.. _cma-es:

===============================================
Covariance Matrix Adaptation Evolution Strategy
===============================================
The Covariance Matrix Adaptation Evolution Strategy (CMA-ES) [Hansen2001]_
implemented in the :mod:`~deap.cma` module makes use of the generate-update
paradigm where a population is generated from a strategy and the strategy is
updated from the population. It is then straight forward to use it for
continuous problem optimization.

As usual the first thing to do is to create the types and as usual we'll need
a minimizing fitness and an individual that is a :class:`list`. A toolbox is
then created with the desired evaluation function.

.. literalinclude:: /../examples/es/cma_minfct.py
   :lines: 28-32

Then, it does not get any harder. Once a :class:`~deap.cma.Strategy` is
instantiated, its :meth:`~deap.cma.Strategy.generate` and
:meth:`~deap.cma.Strategy.update` methods are registered in the toolbox for
uses in the :func:`~deap.algorithms.eaGenerateUpdate` algorithm. The
:meth:`~deap.cma.Strategy.generate` method is set to produce the created
:class:`Individual` class. The random number generator from numpy is seeded
because the :mod:`~deap.cma` module draws all its number from it.

.. literalinclude:: /../examples/es/cma_minfct.py
   :lines: 34,36,37,41-50,52,54

.. [Hansen2001] Hansen and Ostermeier, 2001. Completely Derandomized
   Self-Adaptation in Evolution Strategies. *Evolutionary Computation*
