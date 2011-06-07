Evolutionary Tools
==================
.. automodule:: deap.tools

The :mod:`~deap.tools` module contains the operators for evolutionary
algorithms. They are used to modify, select and move the individuals in their
environment. The set of operators it contains are readily usable in the
:class:`~deap.base.Toolbox`. In addition to the basic operators this module
also contains utility tools to enhance the basic algorithms with
:class:`Statistics`, :class:`HallOfFame`, :class:`Checkpoint`, and
:class:`History`.

Operators
---------
The operator set does the minimum job for transforming or selecting
individuals. This means, for example, that providing two individuals to the
crossover will transform those individuals in-place. The responsibility of
making offspring(s) independent of their parent(s) and invalidating the
fitness is left to the user and is generally fulfilled in the algorithms by
calling :func:`toolbox.clone` on an individuals to duplicate it and ``del`` on
the :attr:`values` attribute of the individual's fitness to invalidate to invalidate this last one.

Initialization
++++++++++++++
Here is a quick table reference to the different implemented initializations
in DEAP. Bellow are the complete descriptions.

===================================== ============ =====================
 Initialization Operator               Input Type   Output Type
===================================== ============ =====================
 :func:`initRepeat`                    sequences    ...
 :func:`initIterate`                   sequences    ...
 :func:`initCycle`                     sequences    ...
 :func:`~deap.gp.genRamped`            sequences    ...
 :func:`~deap.gp.genFull`              sequences    ...
 :func:`~deap.gp.genGrow`              sequences    ...
===================================== ============ =====================

.. autofunction:: deap.tools.initRepeat

.. autofunction:: deap.tools.initIterate

.. autofunction:: deap.tools.initCycle

.. autofunction:: deap.gp.genRamped

.. autofunction:: deap.gp.genFull

.. autofunction:: deap.gp.genGrow

Crossover
+++++++++

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
 :func:`~deap.gp.cxUniformOnePoint`    trees
 :func:`~deap.gp.cxTypedOnePoint`      typed trees
 :func:`~deap.gp.cxKozaOnePoint`       trees
 :func:`~deap.gp.cxTypedKozaOnePoint`  typed trees
===================================== ==================================

.. autofunction:: deap.tools.cxTwoPoints

.. autofunction:: deap.tools.cxOnePoint

.. autofunction:: deap.tools.cxUniform

.. autofunction:: deap.tools.cxPartialyMatched

.. autofunction:: deap.tools.cxUniformPartialyMatched

.. autofunction:: deap.tools.cxBlend

.. autofunction:: deap.tools.cxESBlend(ind1, ind2, alpha[, minstrategy])

.. autofunction:: deap.tools.cxESTwoPoints

.. autofunction:: deap.tools.cxSimulatedBinary

.. autofunction:: deap.tools.cxMessyOnePoint

.. autofunction:: deap.gp.cxUniformOnePoint

.. autofunction:: deap.gp.cxTypedOnePoint

.. autofunction:: deap.gp.cxKozaOnePoint(ind1, ind2, cxtermpb=0.1)

.. autofunction:: deap.gp.cxTypedKozaOnePoint(ind1, ind2, cxtermpb=0.1)

Mutation
++++++++

Here is a quick table reference to the different implemented mutations in 
DEAP. Bellow are the complete descriptions.

========================================= ==================================
 Mutation Operator                         Input Type                      
========================================= ==================================
 :func:`mutGaussian`                       float sequence
 :func:`mutShuffleIndexes`                 sequence                    
 :func:`mutFlipBit`                        binary sequence
 :func:`mutES`                             float sequence with strategy
 :func:`~deap.gp.mutUniform`               tree
 :func:`~deap.gp.mutTypedUniform`          typed tree
 :func:`~deap.gp.mutTypedNodeReplacement`  typed tree
 :func:`~deap.gp.mutTypedEphemeral`        typed tree
 :func:`~deap.gp.mutShrink`                tree
 :func:`~deap.gp.mutTypedInsert`           typed tree
========================================= ==================================

.. autofunction:: deap.tools.mutGaussian

.. autofunction:: deap.tools.mutShuffleIndexes

.. autofunction:: deap.tools.mutFlipBit

.. autofunction:: deap.tools.mutES(individual, indpb[, minstrategy])

.. autofunction:: deap.gp.mutUniform

.. autofunction:: deap.gp.mutTypedUniform

.. autofunction:: deap.gp.mutTypedNodeReplacement

.. autofunction:: deap.gp.mutTypedEphemeral

.. autofunction:: deap.gp.mutShrink

.. autofunction:: deap.gp.mutTypedInsert

Selection
+++++++++

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

.. autofunction:: deap.tools.selTournament

.. autofunction:: deap.tools.selRoulette

.. autofunction:: deap.tools.selNSGA2

.. autofunction:: deap.tools.selSPEA2

.. autofunction:: deap.tools.selRandom

.. autofunction:: deap.tools.selBest

.. autofunction:: deap.tools.selWorst

Migration
+++++++++

Here is a quick table reference to the different implemented migrations in 
DEAP. Bellow are the complete descriptions.

===================================== ==================================
 Selection Operator                    Input Type                      
===================================== ==================================
 :func:`migRing`                       one level multidemic sequence
===================================== ==================================

.. autofunction:: deap.tools.migRing(populations, n, selection[, replacement, migarray, sel_kargs, repl_kargs])

Statistics
----------
.. autoclass:: deap.tools.Statistics([key][, n])
	:members:

.. autofunction:: deap.tools.mean

.. autofunction:: deap.tools.median

.. autofunction:: deap.tools.var

.. autofunction:: deap.tools.std

Hall-Of-Fame
------------
.. autoclass:: deap.tools.HallOfFame

   .. automethod:: deap.tools.HallOfFame.update
   
   .. automethod:: deap.tools.HallOfFame.insert
   
   .. automethod:: deap.tools.HallOfFame.remove
   
   .. automethod:: deap.tools.HallOfFame.clear

.. autoclass:: deap.tools.ParetoFront([similar])

   .. automethod:: deap.tools.ParetoFront.update

Checkpoint
----------
.. autoclass:: deap.tools.Checkpoint([yaml,object[, ...]])
   
   .. automethod:: deap.tools.Checkpoint.dump(prefix)
   
   .. automethod:: deap.tools.Checkpoint.load(filename)
   
   .. automethod:: deap.tools.Checkpoint.add(object[, ...])
   
   .. automethod:: deap.tools.Checkpoint.remove(object[, ...])

History
-------
.. autoclass:: deap.tools.History
   
   .. automethod:: deap.tools.History.populate
   
   .. automethod:: deap.tools.History.update(individual[, ...])
   
   .. autoattribute:: deap.tools.History.decorator