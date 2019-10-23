Algorithms
==========

.. automodule:: deap.algorithms


Complete Algorithms
-------------------
These are complete boxed algorithms that are somewhat limited to the very
basic evolutionary computation concepts.

.. autoclass:: deap.algorithms.GenerationalAlgorithm

.. autoclass:: deap.algorithms.MuLambdaAlgorithm

.. autoclass:: deap.algorithms.GenerateUpdateAlgorithm

Variations
----------
Variations are smaller parts of the algorithms that can be used separately to
build more complex algorithms.

.. autofunction:: deap.algorithms.and_variation

.. autofunction:: deap.algorithms.or_variation

Utils
-----

.. autofunction:: deap.algorithms.evaluate_invalids

Covariance Matrix Adaptation Evolution Strategy
===============================================

.. automodule:: deap.cma

.. autoclass:: deap.cma.Strategy(centroid, sigma[, **kargs])
   :members:

.. autoclass:: deap.cma.StrategyOnePlusLambda(parent, sigma[, **kargs])
   :members:

.. autoclass:: deap.cma.StrategyMultiObjective(population, sigma[, **kargs])
   :members:
