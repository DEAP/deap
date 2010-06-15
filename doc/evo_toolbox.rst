.. _evo-toolbox:

====================
Evolutionary Toolbox
====================

.. automodule:: eap.toolbox

.. autoclass:: eap.toolbox.Toolbox
   
   .. automethod:: register(methodname, method[, content_init[, size_init]], ...)
   
   .. automethod:: unregister(methodname)
   
Operators
=========

This module contains the operators an evolutionary algorithm. They are used to modify, select and move the individuals in their environment. A good set of operators should allow to move from an initial population of good solutions, equivalent to random sampling, to excellent configurations optimizing the studied problem.

.. note::
   Operators that affects the individual's constitution (attributes) are responsible of invalidating the fitness and make sure that the new individual(s) is (are) independent of the original individual(s).


Crossover
---------

General
+++++++

.. autofunction:: eap.toolbox.cxTwoPoints

.. autofunction:: eap.toolbox.cxOnePoint

.. autofunction:: eap.toolbox.cxUniform

Indices
+++++++

.. autofunction:: eap.toolbox.cxPartialyMatched

.. autofunction:: eap.toolbox.cxUniformPartialyMatched

Float
+++++

.. autofunction:: eap.toolbox.cxBlend

.. autofunction:: eap.toolbox.cxSimulatedBinary


Mutation
--------

.. autofunction:: eap.toolbox.mutGaussian

.. autofunction:: eap.toolbox.mutShuffleIndexes

.. autofunction:: eap.toolbox.mutFlipBit


Selection
---------

.. autofunction:: eap.toolbox.selTournament

.. autofunction:: eap.toolbox.selRandom

.. autofunction:: eap.toolbox.selBest

.. autofunction:: eap.toolbox.selWorst

Migration
---------

.. autofunction:: eap.toolbox.migRing(populations, n, selection[, replacement][, migarray][, sel_kargs][, repl_kargs])

