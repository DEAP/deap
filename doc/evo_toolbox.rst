.. _evo-toolbox:

====================
Evolutionary Toolbox
====================

.. automodule:: deap.toolbox

.. autoclass:: deap.toolbox.Toolbox
   
   .. automethod:: register(methodname, method [, ...])
   
   .. automethod:: unregister(methodname)
   
   .. automethod:: decorate(methodname, decorator[, ...])
   
Operators
=========

.. automodule:: deap.operators

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

.. autofunction:: deap.operators.cxTwoPoints

.. autofunction:: deap.operators.cxOnePoint

.. autofunction:: deap.operators.cxUniform

.. autofunction:: deap.operators.cxPartialyMatched

.. autofunction:: deap.operators.cxUniformPartialyMatched

.. autofunction:: deap.operators.cxBlend

.. autofunction:: deap.operators.cxESBlend(ind1, ind2, alpha[, minstrategy])

.. autofunction:: deap.operators.cxESTwoPoints

.. autofunction:: deap.operators.cxSimulatedBinary

.. autofunction:: deap.operators.cxMessyOnePoint

.. autofunction:: deap.operators.cxTreeUniformOnePoint

.. autofunction:: deap.operators.cxTypedTreeOnePoint

.. autofunction:: deap.operators.cxTreeKozaOnePoint(ind1, ind2, cxtermpb=0.1)

.. autofunction:: deap.operators.cxTypedTreeKozaOnePoint(ind1, ind2, cxtermpb=0.1)

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
 :func:`mutTypedTreeNodeReplacement`   typed tree
 :func:`mutTypedTreeEphemeral`         typed tree
 :func:`mutTreeShrink`                 tree
 :func:`mutTypedTreeInsert`            typed tree
===================================== ==================================

.. autofunction:: deap.operators.mutGaussian

.. autofunction:: deap.operators.mutShuffleIndexes

.. autofunction:: deap.operators.mutFlipBit

.. autofunction:: deap.operators.mutES(individual, indpb[, minstrategy])

.. autofunction:: deap.operators.mutTreeUniform

.. autofunction:: deap.operators.mutTypedTreeUniform

.. autofunction:: deap.operators.mutTypedTreeNodeReplacement

.. autofunction:: deap.operators.mutTypedTreeEphemeral

.. autofunction:: deap.operators.mutTreeShrink

.. autofunction:: deap.operators.mutTypedTreeInsert

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

.. autofunction:: deap.operators.selTournament

.. autofunction:: deap.operators.selRoulette

.. autofunction:: deap.operators.selNSGA2

.. autofunction:: deap.operators.selSPEA2

.. autofunction:: deap.operators.selRandom

.. autofunction:: deap.operators.selBest

.. autofunction:: deap.operators.selWorst

Migration
---------

Here is a quick table reference to the different implemented migrations in 
DEAP. Bellow are the complete descriptions.

===================================== ==================================
 Selection Operator                    Input Type                      
===================================== ==================================
 :func:`migRing`                       one level multi-demic sequence
===================================== ==================================

.. autofunction:: deap.operators.migRing(populations, n, selection[, replacement, migarray, sel_kargs, repl_kargs])


Other Tools
===========
.. _other-tools:

This section contains references to helper functions found in the toolbox.
For the moment, users are refered to the examples for how to use those tools.

Initialization
--------------

.. autoclass:: deap.toolbox.Repeat

:class:`Repeat` is used in the ``examples/ga_onemax.py`` example.

.. autoclass:: deap.toolbox.Iterate

:class:`Iterate` is used in the ``examples/ga_tsp.py`` example.

.. autoclass:: deap.toolbox.FuncCycle

:class:`FuncCycle` is used in the ``examples/gp_adf_symbreg.py`` example.

Decoration
----------

.. autofunction:: deap.toolbox.decorate
