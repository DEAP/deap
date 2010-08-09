.. _evo-toolbox:

====================
Evolutionary Toolbox
====================

.. automodule:: eap.toolbox

.. autoclass:: eap.toolbox.Toolbox
   
   .. automethod:: register(methodname, method[, content_init[, size_init]], ...)
   
   .. automethod:: unregister(methodname)
   
   .. automethod:: decorate(methodname, decorator[, ...])
   
Operators
=========

This module contains the operators an evolutionary algorithm. They are used to modify, select and move the individuals in their environment. A good set of operators should allow to move from an initial population of good solutions, equivalent to random sampling, to excellent configurations optimizing the studied problem.

.. note::
   The responsibility of making offspring(s) independent of their parent(s) and invalidating the fitness is left to the user and is generally fulfilled using respectively the :func:`~eap.toolbox.deepcopyArgs` and :func:`~eap.toolbox.delFitness` decorators. 



Crossover
---------

.. autofunction:: eap.toolbox.cxTwoPoints

.. autofunction:: eap.toolbox.cxOnePoint

.. autofunction:: eap.toolbox.cxUniform

.. autofunction:: eap.toolbox.cxPartialyMatched

.. autofunction:: eap.toolbox.cxUniformPartialyMatched

.. autofunction:: eap.toolbox.cxBlend

.. autofunction:: eap.toolbox.cxESBlend

.. autofunction:: eap.toolbox.cxESTwoPoints

.. autofunction:: eap.toolbox.cxSimulatedBinary

.. autofunction:: eap.toolbox.cxMessyOnePoint

.. autofunction:: eap.toolbox.cxTreeUniformOnePoint

.. autofunction:: eap.toolbox.cxTypedTreeOnePoint



Mutation
--------

.. autofunction:: eap.toolbox.mutGaussian

.. autofunction:: eap.toolbox.mutShuffleIndexes

.. autofunction:: eap.toolbox.mutFlipBit

.. autofunction:: eap.toolbox.mutES

.. autofunction:: eap.toolbox.mutTreeUniform

.. autofunction:: eap.toolbox.mutTypedTreeUniform

Selection
---------

.. autofunction:: eap.toolbox.selTournament

.. autofunction:: eap.toolbox.selRoulette

.. autofunction:: eap.toolbox.nsga2

.. autofunction:: eap.toolbox.spea2

.. autofunction:: eap.toolbox.selRandom

.. autofunction:: eap.toolbox.selBest

.. autofunction:: eap.toolbox.selWorst

Migration
---------

.. autofunction:: eap.toolbox.migRing(populations, n, selection[, replacement][, migarray][, sel_kargs][, repl_kargs])

Decorators
----------
The toolbox also contains some basic decorators to enhance operator's functionality.

.. autofunction:: eap.toolbox.deepcopyArgs(argname[, ...])

.. autofunction:: eap.toolbox.decorate