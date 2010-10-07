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

This module contains the operators for an evolutionary algorithm. They are used to modify, select and move the individuals in their environment. A good set of operators should allow to move from an initial population of good solutions, equivalent to random sampling, to excellent configurations optimizing the studied problem.

.. note::
   The responsibility of making offspring(s) independent of their parent(s) and invalidating the fitness is left to the user and is generally fulfilled in the algorithms by calling toolbox.clone on an individuals to duplicate it and del on the values attribute of the individual's fitness.

.. versionchanged:: 0.6
   In earlier versions, the resposability of cloning the individuals was left to the operator that wanted to modify an individuals. The new offsprings were returned via a tuple and the parents were left intact. In version 0.6, cloning is made prior to the operation on the individuals and the operators can now modify the individuals directly. At a user level, this may not affect your evolution if you were using the algorithms, but if you developped your own algorithms, you better take a look at the changes made in the algorithms source code.

Crossover
---------

.. autofunction:: eap.toolbox.cxTwoPoints

.. autofunction:: eap.toolbox.cxOnePoint

.. autofunction:: eap.toolbox.cxUniform

.. autofunction:: eap.toolbox.cxPartialyMatched

.. autofunction:: eap.toolbox.cxUniformPartialyMatched

.. autofunction:: eap.toolbox.cxBlend

.. autofunction:: eap.toolbox.cxESBlend(ind1, ind2, alpha[, minstrategy])

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

.. autofunction:: eap.toolbox.mutES(individual, indpb[, minstrategy])

.. autofunction:: eap.toolbox.mutTreeUniform

.. autofunction:: eap.toolbox.mutTypedTreeUniform

.. autofunction:: eap.toolbox.mutTypedTreeNodeReplacement

.. autofunction:: eap.toolbox.mutTypedTreeEphemeral

.. autofunction:: eap.toolbox.mutTreeShrink

.. autofunction:: eap.toolbox.mutTypedTreeInsert

.. .. autofunction:: eap.toolbox.mutTreeRandomMethod

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

.. autofunction:: eap.toolbox.migRing(populations, n, selection[, replacement, migarray, sel_kargs, repl_kargs])

Decoration
----------

.. autofunction:: eap.toolbox.decorate