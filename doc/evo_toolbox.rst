.. _evo-toolbox:

====================
Evolutionary Toolbox
====================

.. automodule:: eap.toolbox

.. autoclass:: eap.toolbox.Toolbox
   
   .. automethod:: register(methodname, method [, ...])
   
   .. automethod:: unregister(methodname)
   
   .. automethod:: decorate(methodname, decorator[, ...])
   
Operators
=========

.. automodule:: eap.operators

This module contains the operators for an evolutionary algorithm. They are
used to modify, select and move the individuals in their environment. A good
set of operators should allow to move from an initial population of good
solutions, equivalent to random sampling, to excellent configurations
optimizing the studied problem.

.. note:: The responsibility of making offspring(s) independent of their
   parent(s) and invalidating the fitness is left to the user and is generally
   fulfilled in the algorithms by calling :func:`toolbox.clone` on an 
   individuals to duplicate it and ``del`` on the values attribute of the 
   individual's fitness.

.. versionchanged:: 0.6
   In earlier versions, the resposability of cloning the individuals was left
   to the operator that wanted to modify an individuals. The new offsprings
   were returned via a tuple and the parents were left intact. In version 0.6,
   cloning is made prior to the operation on the individuals and the operators
   can now modify the individuals directly. At a user level, this may not
   affect your evolution if you were using the algorithms, but if you
   developped your own algorithms, you better take a look at the changes made
   in the algorithms source code.

Crossover
---------

Here is a quick table reference to the different implemented crossovers in 
DEAP. Bellow are the complete descriptions.

===================================== ==================================
 Crossover Operator                    Input Type                      
===================================== ==================================
 :func:`cxOnePoint`                    sequences                    
 :func:`cxTwoPoints`                   sequences                    
 :func:`cxUniform`                     sequences
 :func:`cxPartialyMatched`             integer sequences
 :func:`cxUniformPartialyMatched`      integer sequences
 :func:`cxBlend`                       float sequences
 :func:`cxESBlend`                     float sequences with strategy
 :func:`cxESTwoPoints`                 sequences with strategy
 :func:`cxSimulatedBinary`             float sequences
 :func:`cxMessyOnePoint`               sequences
 :func:`cxTreeUniformOnePoint`         trees
 :func:`cxTypedTreeOnePoint`           typed trees
 :func:`cxTreeKozaOnePoint`            trees
 :func:`cxTypedTreeKozaOnePoint`       typed trees
===================================== ==================================

.. autofunction:: eap.operators.cxTwoPoints

.. autofunction:: eap.operators.cxOnePoint

.. autofunction:: eap.operators.cxUniform

.. autofunction:: eap.operators.cxPartialyMatched

.. autofunction:: eap.operators.cxUniformPartialyMatched

.. autofunction:: eap.operators.cxBlend

.. autofunction:: eap.operators.cxESBlend(ind1, ind2, alpha[, minstrategy])

.. autofunction:: eap.operators.cxESTwoPoints

.. autofunction:: eap.operators.cxSimulatedBinary

.. autofunction:: eap.operators.cxMessyOnePoint

.. autofunction:: eap.operators.cxTreeUniformOnePoint

.. autofunction:: eap.operators.cxTypedTreeOnePoint

.. autofunction:: eap.operators.cxTreeKozaOnePoint(ind1, ind2, cxtermpb=0.1)

.. autofunction:: eap.operators.cxTypedTreeKozaOnePoint(ind1, ind2, cxtermpb=0.1)

Mutation
--------

Here is a quick table reference to the different implemented mutations in 
DEAP. Bellow are the complete descriptions.

===================================== ==================================
 Mutation Operator                     Input Type                      
===================================== ==================================
 :func:`mutGaussian`                   float sequence
 :func:`mutShuffleIndexes`             sequence                    
 :func:`mutFlipBit`                    binary sequence
 :func:`mutES`                         float sequence with strategy
 :func:`mutTreeUniform`                tree
 :func:`mutTypedTreeUniform`           typed tree
 :func:`mutTypedTreeEphemeral`         typed tree
 :func:`mutTreeShrink`                 tree
 :func:`mutTypedTreeInsert`            typed tree
===================================== ==================================

.. autofunction:: eap.operators.mutGaussian

.. autofunction:: eap.operators.mutShuffleIndexes

.. autofunction:: eap.operators.mutFlipBit

.. autofunction:: eap.operators.mutES(individual, indpb[, minstrategy])

.. autofunction:: eap.operators.mutTreeUniform

.. autofunction:: eap.operators.mutTypedTreeUniform

.. autofunction:: eap.operators.mutTypedTreeNodeReplacement

.. autofunction:: eap.operators.mutTypedTreeEphemeral

.. autofunction:: eap.operators.mutTreeShrink

.. autofunction:: eap.operators.mutTypedTreeInsert

Selection
---------

Here is a quick table reference to the different implemented selections in 
DEAP. Bellow are the complete descriptions.

===================================== ==================================
 Selection Operator                    Input Type                      
===================================== ==================================
 :func:`selTournament`                 multi-objective sequence
 :func:`selRoulette`                   mono-objective sequence
 :func:`selNSGA2`                      multi-objective sequence
 :func:`selSPEA2`                      multi-objective sequence
 :func:`selRandom`                     multi-objective sequence
 :func:`selBest`                       multi-objective sequence
 :func:`selWorst`                      multi-objective sequence
===================================== ==================================

.. autofunction:: eap.operators.selTournament

.. autofunction:: eap.operators.selRoulette

.. autofunction:: eap.operators.selNSGA2

.. autofunction:: eap.operators.selSPEA2

.. autofunction:: eap.operators.selRandom

.. autofunction:: eap.operators.selBest

.. autofunction:: eap.operators.selWorst

Migration
---------

Here is a quick table reference to the different implemented migrations in 
DEAP. Bellow are the complete descriptions.

===================================== ==================================
 Selection Operator                    Input Type                      
===================================== ==================================
 :func:`migRing`                       one level multi-demic sequence
===================================== ==================================

.. autofunction:: eap.operators.migRing(populations, n, selection[, replacement, migarray, sel_kargs, repl_kargs])


Other Tools
===========
.. _other-tools:

This section contains references to helper functions found in the toolbox.
For the moment, users are refered to the examples for how to use those tools.

Initialization
--------------

.. autoclass:: eap.toolbox.Repeat

:class:`Repeat` is used in the ``examples/ga_onemax.py`` example.

.. autoclass:: eap.toolbox.Iterate

:class:`Iterate` is used in the ``examples/ga_tsp.py`` example.

.. autoclass:: eap.toolbox.FuncCycle

:class:`FuncCycle` is used in the ``examples/gp_adf_symbreg.py`` example.

Decoration
----------

.. autofunction:: eap.toolbox.decorate
