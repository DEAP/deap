====================
Evolutionary Toolbox
====================

.. automodule:: eap.evolutiontoolbox

.. autoclass:: EvolutionToolbox
   :members:
   
.. autoclass:: SimpleGAToolbox
   :members:
   
.. autoclass:: IndicesGAToolbox
   :members:
   
Operators
=========

.. automodule:: eap.operators 

Crossover
---------

.. autofunction:: eap.operators.twoPointsCx

.. autofunction:: eap.operators.onePointCx

.. autofunction:: eap.operators.pmxCx

Mutation
--------

.. autofunction:: eap.operators.gaussMut(individual, mu, sigma, mutIndxPb=0.3)

.. autofunction:: eap.operators.shuffleIndxMut(individual, shuffleIndxPb=0.3)

.. autofunction:: eap.operators.flipBitMut(individual, flipIndxPb=0.3)

Selection
---------

.. autofunction:: eap.operators.tournSel

.. autofunction:: eap.operators.rndSel

.. autofunction:: eap.operators.bestSel

.. autofunction:: eap.operators.worstSel

Migration
---------

Migration is not fully implemented yet.

