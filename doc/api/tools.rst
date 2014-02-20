Evolutionary Tools
==================
.. automodule:: deap.tools

.. _operators:

Operators
---------
The operator set does the minimum job for transforming or selecting
individuals. This means, for example, that providing two individuals to the
crossover will transform those individuals in-place. The responsibility of
making offspring(s) independent of their parent(s) and invalidating the
fitness is left to the user and is generally fulfilled in the algorithms by
calling :func:`toolbox.clone` on an individual to duplicate it and 
``del`` on the :attr:`values` attribute of the individual's fitness to 
invalidate it.

Here is a list of the implemented operators in DEAP,

============================ =========================================== ========================================= ============================ ================
 Initialization               Crossover                                   Mutation                                  Selection                   Migration 
============================ =========================================== ========================================= ============================ ================
 :func:`initRepeat`           :func:`cxOnePoint`                          :func:`mutGaussian`                       :func:`selTournament`       :func:`migRing`
 :func:`initIterate`          :func:`cxTwoPoint`                          :func:`mutShuffleIndexes`                 :func:`selRoulette`         ..             
 :func:`initCycle`            :func:`cxUniform`                           :func:`mutFlipBit`                        :func:`selNSGA2`            ..             
 ..                           :func:`cxPartialyMatched`                   :func:`mutPolynomialBounded`              :func:`selSPEA2`            ..             
 ..                           :func:`cxUniformPartialyMatched`            :func:`mutUniformInt`                     :func:`selRandom`           ..             
 ..                           :func:`cxOrdered`                           :func:`mutESLogNormal`                    :func:`selBest`             ..             
 ..                           :func:`cxBlend`                             ..                                        :func:`selWorst`            ..             
 ..                           :func:`cxESBlend`                           ..                                        :func:`selTournamentDCD`    ..             
 ..                           :func:`cxESTwoPoint`                        ..                                        :func:`selDoubleTournament` ..             
 ..                           :func:`cxSimulatedBinary`                   ..                                        ..                          ..             
 ..                           :func:`cxSimulatedBinaryBounded`            ..                                        ..                          ..             
 ..                           :func:`cxMessyOnePoint`                     ..                                        ..                          ..             
============================ =========================================== ========================================= ============================ ================

and genetic programming specific operators.

================================ =========================================== ========================================= ================================
 Initialization                   Crossover                                   Mutation                                  Bloat control
================================ =========================================== ========================================= ================================
 :func:`~deap.gp.genFull`         :func:`~deap.gp.cxOnePoint`                 :func:`~deap.gp.mutShrink`                :func:`~deap.gp.staticLimit`
 :func:`~deap.gp.genGrow`         :func:`~deap.gp.cxOnePointLeafBiased`       :func:`~deap.gp.mutUniform`               :func:`selDoubleTournament`
 :func:`~deap.gp.genHalfAndHalf`  ..                                          :func:`~deap.gp.mutNodeReplacement`       ..
 ..                               ..                                          :func:`~deap.gp.mutEphemeral`             ..
 ..                               ..                                          :func:`~deap.gp.mutInsert`                ..
================================ =========================================== ========================================= ================================


Initialization
++++++++++++++

.. autofunction:: deap.tools.initRepeat

.. autofunction:: deap.tools.initIterate

.. autofunction:: deap.tools.initCycle

.. autofunction:: deap.gp.genFull

.. autofunction:: deap.gp.genGrow

.. autofunction:: deap.gp.genHalfAndHalf

.. autofunction:: deap.gp.genRamped

Crossover
+++++++++

.. autofunction:: deap.tools.cxOnePoint

.. autofunction:: deap.tools.cxTwoPoint

.. autofunction:: deap.tools.cxTwoPoints

.. autofunction:: deap.tools.cxUniform

.. autofunction:: deap.tools.cxPartialyMatched

.. autofunction:: deap.tools.cxUniformPartialyMatched

.. autofunction:: deap.tools.cxOrdered

.. autofunction:: deap.tools.cxBlend

.. autofunction:: deap.tools.cxESBlend

.. autofunction:: deap.tools.cxESTwoPoint

.. autofunction:: deap.tools.cxESTwoPoints

.. autofunction:: deap.tools.cxSimulatedBinary

.. autofunction:: deap.tools.cxSimulatedBinaryBounded

.. autofunction:: deap.tools.cxMessyOnePoint

.. autofunction:: deap.gp.cxOnePoint

.. autofunction:: deap.gp.cxOnePointLeafBiased

Mutation
++++++++

.. autofunction:: deap.tools.mutGaussian

.. autofunction:: deap.tools.mutShuffleIndexes

.. autofunction:: deap.tools.mutFlipBit

.. autofunction:: deap.tools.mutUniformInt

.. autofunction:: deap.tools.mutPolynomialBounded

.. autofunction:: deap.tools.mutESLogNormal

.. autofunction:: deap.gp.mutShrink

.. autofunction:: deap.gp.mutUniform

.. autofunction:: deap.gp.mutNodeReplacement

.. autofunction:: deap.gp.mutEphemeral

.. autofunction:: deap.gp.mutInsert

Selection
+++++++++

.. autofunction:: deap.tools.selTournament

.. autofunction:: deap.tools.selRoulette

.. autofunction:: deap.tools.selNSGA2

.. autofunction:: deap.tools.selSPEA2

.. autofunction:: deap.tools.selRandom

.. autofunction:: deap.tools.selBest

.. autofunction:: deap.tools.selWorst

.. autofunction:: deap.tools.selDoubleTournament

.. autofunction:: deap.tools.selTournamentDCD

.. autofunction:: deap.tools.sortNondominated

.. autofunction:: deap.tools.sortLogNondominated

Bloat control
+++++++++++++

.. autofunction:: deap.gp.staticLimit

Migration
+++++++++

.. autofunction:: deap.tools.migRing(populations, k, selection[, replacement, migarray])

Statistics
----------
.. autoclass:: deap.tools.Statistics([key])
	:members:

.. autoclass:: deap.tools.MultiStatistics(**kargs)
	:members:

Logbook
-------

.. autoclass:: deap.tools.Logbook
   :members:

Hall-Of-Fame
------------
.. autoclass:: deap.tools.HallOfFame

   .. automethod:: deap.tools.HallOfFame.update
   
   .. automethod:: deap.tools.HallOfFame.insert
   
   .. automethod:: deap.tools.HallOfFame.remove
   
   .. automethod:: deap.tools.HallOfFame.clear

.. autoclass:: deap.tools.ParetoFront([similar])

   .. automethod:: deap.tools.ParetoFront.update


History
-------
.. autoclass:: deap.tools.History

   .. automethod:: deap.tools.History.update

   .. autoattribute:: deap.tools.History.decorator

   .. automethod:: deap.tools.History.getGenealogy(individual[, max_depth])

