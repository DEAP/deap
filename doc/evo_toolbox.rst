====================
Evolutionary Toolbox
====================

.. automodule:: eap.toolbox

.. autoclass:: Toolbox
   :members:
   
Operators
=========

This module contains the operators an evolutionary algorithm. They are used to modify, select and move the individuals in their environment. A good set of operators should allow to move from an initial population of good solutions, equivalent to random sampling, to excellent configurations optimizing the studied problem.

.. note::
   Operators that affects the individual's constitution (attributes) are responsible of invalidating the fitness and make sure that the new individual(s) is (are) independent of the original individual(s).

Crossover
---------

.. autofunction:: twoPointsCx

.. autofunction:: onePointCx

.. autofunction:: pmCx

.. autofunction:: blendESCx

   .. versionadded:: 0.3.1a

Mutation
--------

.. autofunction:: gaussMut

.. autofunction:: shuffleIndxMut

.. autofunction:: flipBitMut

.. autofunction:: gaussESMut

   .. versionadded:: 0.3.1a

Selection
---------

.. autofunction:: tournSel

.. autofunction:: rndSel

.. autofunction:: bestSel

.. autofunction:: worstSel

Migration
---------

.. autofunction:: ringMig

