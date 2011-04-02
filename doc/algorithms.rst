Algorithms
==========

.. automodule:: eap.algorithms
   
.. autofunction:: eap.algorithms.eaSimple(toolbox, population, cxpb, mutpb, ngen[, stats, halloffame])

.. autofunction:: eap.algorithms.varSimple
   
.. autofunction:: eap.algorithms.eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame])

.. autofunction:: eap.algorithms.eaMuCommaLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen[, stats, halloffame])

.. autofunction:: eap.algorithms.varMuLambda

.. autofunction:: eap.algorithms.eaSteadyState(toolbox, population, ngen[, stats, halloffame])

.. autofunction:: eap.algorithms.varSteadyState

Covariance Matrix Adaptation Evolution Strategy
===============================================

.. autofunction:: eap.cma.esCMA(toolbox, population, sigma, ngen[, halloffame, **kargs])

.. autoclass:: eap.cma.CMAStrategy(population, sigma[, params])
   :members: