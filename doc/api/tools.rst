Evolutionary Tools
==================
.. automodule:: deap.tools

Operators
---------
The operator set does the minimum job for transforming or selecting
individuals. This means, for example, that providing two individuals to the
crossover will transform those individuals in-place. The responsibility of
making offspring(s) independent of their parent(s) and invalidating the
fitness is left to the user and is generally fulfilled in the algorithms by
calling :func:`toolbox.clone` on an individuals to duplicate it and ``del`` on
the :attr:`values` attribute of the individual's fitness to invalidate to invalidate this last one.

Here is a list of the implemented operators in DEAP.

============================ =========================================== ========================================= ======================= ================
 Initialization               Crossover                                   Mutation                                  Selection               Migration 
============================ =========================================== ========================================= ======================= ================
 :func:`initRepeat`           :func:`cxOnePoint`                          :func:`mutGaussian`                       :func:`selTournament`   :func:`migRing` 
 :func:`initIterate`          :func:`cxTwoPoints`                         :func:`mutShuffleIndexes`                 :func:`selRoulette`     ..             
 :func:`initCycle`            :func:`cxUniform`                           :func:`mutFlipBit`                        :func:`selNSGA2`        ..             
 :func:`~deap.gp.genFull`     :func:`cxPartialyMatched`                   :func:`mutUniformInt`                     :func:`selSPEA2`        ..             
 :func:`~deap.gp.genGrow`     :func:`cxUniformPartialyMatched`            :func:`mutESLogNormal`                    :func:`selRandom`       ..             
 :func:`~deap.gp.genRamped`   :func:`cxOrdered`                           :func:`~deap.gp.mutUniform`               :func:`selBest`         ..             
 ..                           :func:`cxBlend`                             :func:`~deap.gp.mutTypedUniform`          :func:`selWorst`        ..             
 ..                           :func:`cxESBlend`                           :func:`~deap.gp.mutTypedNodeReplacement`  ..                      ..             
 ..                           :func:`cxESTwoPoints`                       :func:`~deap.gp.mutTypedEphemeral`        ..                      ..             
 ..                           :func:`cxSimulatedBinary`                   :func:`~deap.gp.mutShrink`                ..                      ..             
 ..                           :func:`cxSimulatedBinaryBounded`            :func:`~deap.gp.mutTypedInsert`           ..                      ..             
 ..                           :func:`cxMessyOnePoint`                     ..                                        ..                      ..             
 ..                           :func:`~deap.gp.cxUniformOnePoint`          ..                                        ..                      ..             
 ..                           :func:`~deap.gp.cxTypedOnePoint`            ..                                        ..                      ..             
 ..                           :func:`~deap.gp.cxOnePointLeafBiased`       ..                                        ..                      ..             
 ..                           :func:`~deap.gp.cxTypedOnePointLeafBiased`  ..                                        ..                      ..             
============================ =========================================== ========================================= ======================= ================

Initialization
++++++++++++++

.. autofunction:: deap.tools.initRepeat

.. autofunction:: deap.tools.initIterate

.. autofunction:: deap.tools.initCycle

.. autofunction:: deap.gp.genFull

.. autofunction:: deap.gp.genGrow

.. autofunction:: deap.gp.genRamped

Crossover
+++++++++

.. autofunction:: deap.tools.cxOnePoint

.. autofunction:: deap.tools.cxTwoPoints

.. autofunction:: deap.tools.cxUniform

.. autofunction:: deap.tools.cxPartialyMatched

.. autofunction:: deap.tools.cxUniformPartialyMatched

.. autofunction:: deap.tools.cxOrdered

.. autofunction:: deap.tools.cxBlend

.. autofunction:: deap.tools.cxESBlend

.. autofunction:: deap.tools.cxESTwoPoints

.. autofunction:: deap.tools.cxSimulatedBinary

.. autofunction:: deap.tools.cxSimulatedBinaryBounded

.. autofunction:: deap.tools.cxMessyOnePoint

.. autofunction:: deap.gp.cxUniformOnePoint

.. autofunction:: deap.gp.cxTypedOnePoint

.. autofunction:: deap.gp.cxOnePointLeafBiased

.. autofunction:: deap.gp.cxTypedOnePointLeafBiased

Mutation
++++++++

.. autofunction:: deap.tools.mutGaussian

.. autofunction:: deap.tools.mutShuffleIndexes

.. autofunction:: deap.tools.mutFlipBit

.. autofunction:: deap.tools.mutUniformInt

.. autofunction:: deap.tools.mutESLogNormal

.. autofunction:: deap.gp.mutUniform

.. autofunction:: deap.gp.mutTypedUniform

.. autofunction:: deap.gp.mutTypedNodeReplacement

.. autofunction:: deap.gp.mutTypedEphemeral

.. autofunction:: deap.gp.mutShrink

.. autofunction:: deap.gp.mutTypedInsert

Selection
+++++++++

.. autofunction:: deap.tools.selTournament

.. autofunction:: deap.tools.selRoulette

.. autofunction:: deap.tools.selNSGA2

.. autofunction:: deap.tools.selSPEA2

.. autofunction:: deap.tools.selRandom

.. autofunction:: deap.tools.selBest

.. autofunction:: deap.tools.selWorst

Migration
+++++++++

.. autofunction:: deap.tools.migRing(populations, k, selection[, replacement, migarray])

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

Evolution Logger
----------------
.. autoclass:: deap.tools.EvolutionLogger([col_names][, precision])

   .. automethod:: deap.tools.EvolutionLogger.logHeader

   .. automethod:: deap.tools.EvolutionLogger.logGeneration([stats[, index]][, data[, ...]])
   
..   .. autoattribute:: deap.tools.EvolutionLogger.output

Checkpoint
----------
.. autoclass:: deap.tools.Checkpoint()
   
   .. automethod:: deap.tools.Checkpoint.dump(filestream)
   
   .. automethod:: deap.tools.Checkpoint.load(filestream)
   
   .. automethod:: deap.tools.Checkpoint.add(name, object[, key])
   
   .. automethod:: deap.tools.Checkpoint.remove(name[, ...])

History
-------
.. autoclass:: deap.tools.History

   .. automethod:: deap.tools.History.update

   .. autoattribute:: deap.tools.History.decorator

   .. automethod:: deap.tools.History.getGenealogy(individual[, max_depth])

