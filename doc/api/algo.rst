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

.. autofunction:: deap.algorithms.take

Covariance Matrix Adaptation Evolution Strategy
===============================================
.. automodule:: deap.cma

.. currentmodule:: deap.cma

.. autosummary::
   :nosignatures:

   deap.cma.BasicStrategy
   deap.cma.OnePlusLambdaStrategy
   deap.cma.ActiveOnePlusLambdaStrategy
   deap.cma.MultiObjectiveStrategy


.. autoclass:: BasicStrategy(centroid, sigma[, **kargs])
   :members:

.. autoclass:: OnePlusLambdaStrategy(parent, sigma[, **kargs])
   :members:

.. autoclass:: ActiveOnePlusLambdaStrategy(parent, sigma[, **kargs])
   :members:

.. autoclass:: MultiObjectiveStrategy(population, sigma[, **kargs])
   :members:
