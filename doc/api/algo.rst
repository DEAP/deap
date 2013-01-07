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
the population, and a boolean `verbose` to specify wether to
log what is happening during the evolution or not.

.. autofunction:: deap.algorithms.eaSimple(population, toolbox, cxpb, mutpb, ngen[, stats, halloffame, verbose])

.. autofunction:: deap.algorithms.eaMuPlusLambda(population, toolbox, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame, verbose])

.. autofunction:: deap.algorithms.eaMuCommaLambda(population, toolbox, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame, verbose])

.. autofunction:: deap.algorithms.eaGenerateUpdate(toolbox, ngen[, stats, halloffame, verbose])

Variations
----------
Variations are smaller parts of the algorithms that can be used separately to
build more complex algorithms.

.. autofunction:: deap.algorithms.varAnd

.. autofunction:: deap.algorithms.varOr

Covariance Matrix Adaptation Evolution Strategy
===============================================

.. automodule:: deap.cma

.. autoclass:: deap.cma.Strategy(centroid, sigma[, **kargs])
   :members:

.. autoclass:: deap.cma.StrategyOnePlusLambda(parent, sigma[, **kargs])
   :members:
