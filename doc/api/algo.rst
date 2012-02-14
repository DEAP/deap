Algorithms
==========

.. automodule:: deap.algorithms
   

Complete Algorithms
-------------------
These are complete boxed algorithms that are somewhat limited to the very
basic evolutionary computation concepts. All algorithms accept, in addition to
their arguments, an initialized :class:`~deap.tools.Statistics` object to
maintain stats of the evolution, an initialized
:class:`~deap.tools.HallOfFame` to hold the best individual(s) to appear in
the population, and/or an initialized :class:`~deap.tools.EvolutionLogger` to
log what is happening during the evolution.

.. autofunction:: deap.algorithms.eaSimple(toolbox, population, cxpb, mutpb, ngen[, stats, halloffame, logger])

.. autofunction:: deap.algorithms.eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame, logger])

.. autofunction:: deap.algorithms.eaMuCommaLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame, logger])

.. autofunction:: deap.algorithms.eaSteadyState(toolbox, population, ngen[, stats, halloffame, logger])

   .. deprecated:: 0.8
      Use :func:`~deap.algorithms.eaMuPlusLambda` algorithm with :math:`\lambda=1`.

Variations
----------
Variations are smaller parts of the algorithms that can be used separately to
build more complex algorithms.

.. autofunction:: deap.algorithms.varAnd

.. autofunction:: deap.algorithms.varOr

.. autofunction:: deap.algorithms.varSimple

   .. deprecated:: 0.8
      Use function :func:`~deap.algorithms.varAnd` instead.

.. autofunction:: deap.algorithms.varLambda

   .. deprecated:: 0.8
      Use function :func:`~deap.algorithms.varOr` instead.

.. autofunction:: deap.algorithms.varSteadyState

   .. deprecated:: 0.8
      Use function :func:`~deap.algorithms.varOr` instead.

Covariance Matrix Adaptation Evolution Strategy
===============================================

.. automodule:: deap.cma

.. autofunction:: deap.cma.esCMA(toolbox, population, sigma, ngen[, stats, halloffame, logger])

.. autoclass:: deap.cma.Strategy(centroid, sigma[, **kargs])
   :members:

.. .. autoclass:: deap.cma.StrategyOnePlusLambda(parent, sigma[, **kargs])
..    :members:
