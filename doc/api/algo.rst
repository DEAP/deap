Algorithms
==========

.. automodule:: deap.algorithms
   
.. autofunction:: deap.algorithms.eaSimple(toolbox, population, cxpb, mutpb, ngen[, stats, halloffame])

.. autofunction:: deap.algorithms.varSimple

.. autofunction:: deap.algorithms.varAnd
   
.. autofunction:: deap.algorithms.eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame])

.. autofunction:: deap.algorithms.eaMuCommaLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame])

.. autofunction:: deap.algorithms.varLambda

.. autofunction:: deap.algorithms.varOr

.. autofunction:: deap.algorithms.eaSteadyState(toolbox, population, ngen[, stats, halloffame])

.. autofunction:: deap.algorithms.varSteadyState

Covariance Matrix Adaptation Evolution Strategy
===============================================

.. autofunction:: deap.cma.esCMA(toolbox, population, sigma, ngen[, halloffame, **kargs])

.. autoclass:: deap.cma.CMAStrategy(population, sigma[, params])
   :members: