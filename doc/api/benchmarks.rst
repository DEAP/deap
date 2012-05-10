==========
Benchmarks
==========

.. automodule:: deap.benchmarks

============================= ============================= ====================
Single Objective Continuous   Multi Objective Continuous    Binary              
============================= ============================= ====================
:func:`cigar`                 :func:`fonseca`               :func:`~binary.chuang_f1`
:func:`plane`                 :func:`kursawe`               :func:`~binary.chuang_f2`
:func:`sphere`                :func:`schaffer_mo`           :func:`~binary.chuang_f3`
:func:`rand`                  :func:`dtlz1`                 :func:`~binary.royal_road1`
:func:`ackley`                :func:`dtlz2`                 :func:`~binary.royal_road2`
:func:`bohachevsky`           :func:`dtlz3`                 ..
:func:`griewank`              :func:`dtlz4`                 ..
:func:`h1`                    :func:`zdt1`                  ..
:func:`himmelblau`            :func:`zdt2`                  ..
:func:`rastrigin`             :func:`zdt3`                  ..
:func:`rastrigin_scaled`      :func:`zdt4`                  ..
:func:`rastrigin_skew`        :func:`zdt6`                  ..
:func:`rosenbrock`            ..                            ..
:func:`schaffer`              ..                            ..
:func:`schwefel`              ..                            ..
:func:`shekel`                ..                            .. 
============================= ============================= ====================

Continuous Optimization
=======================

.. autofunction:: deap.benchmarks.cigar

.. autofunction:: deap.benchmarks.plane

.. autofunction:: deap.benchmarks.sphere

.. autofunction:: deap.benchmarks.rand

.. autofunction:: deap.benchmarks.ackley

.. autofunction:: deap.benchmarks.bohachevsky

.. autofunction:: deap.benchmarks.griewank

.. autofunction:: deap.benchmarks.h1

.. autofunction:: deap.benchmarks.himmelblau

.. autofunction:: deap.benchmarks.rastrigin

.. autofunction:: deap.benchmarks.rastrigin_scaled

.. autofunction:: deap.benchmarks.rastrigin_skew

.. autofunction:: deap.benchmarks.rosenbrock

.. autofunction:: deap.benchmarks.schaffer

.. autofunction:: deap.benchmarks.schwefel

.. autofunction:: deap.benchmarks.shekel

Multi-objective
---------------

.. autofunction:: deap.benchmarks.fonseca

.. autofunction:: deap.benchmarks.kursawe

.. autofunction:: deap.benchmarks.schaffer_mo

.. autofunction:: deap.benchmarks.dtlz1

.. autofunction:: deap.benchmarks.dtlz2

.. autofunction:: deap.benchmarks.dtlz3

.. autofunction:: deap.benchmarks.dtlz4

.. autofunction:: deap.benchmarks.zdt1

.. autofunction:: deap.benchmarks.zdt2

.. autofunction:: deap.benchmarks.zdt3

.. autofunction:: deap.benchmarks.zdt4

.. autofunction:: deap.benchmarks.zdt6

Binary Optimization
===================

.. automodule:: deap.benchmarks.binary

.. autofunction:: deap.benchmarks.binary.chuang_f1

.. autofunction:: deap.benchmarks.binary.chuang_f2

.. autofunction:: deap.benchmarks.binary.chuang_f3

.. autofunction:: deap.benchmarks.binary.royal_road1

.. autofunction:: deap.benchmarks.binary.royal_road2

.. autofunction:: deap.benchmarks.binary.bin2float

Moving Peaks Benchmark
======================

.. automodule:: deap.benchmarks.movingpeaks

.. autoclass:: deap.benchmarks.movingpeaks.MovingPeaks(self, dim[, pfunc][, npeaks][, bfunc][, random][, ...])
   :members:

.. autofunction:: deap.benchmarks.movingpeaks.cone

.. autofunction:: deap.benchmarks.movingpeaks.function1
   
Benchmarks tools
================

.. automodule:: deap.benchmarks.tools
   :members: convergence, diversity
   
.. autofunction:: deap.benchmarks.tools.noise

   .. automethod:: deap.benchmarks.tools.noise.noise
      
.. autofunction:: deap.benchmarks.tools.rotate

   .. automethod:: deap.benchmarks.tools.rotate.rotate

.. autofunction:: deap.benchmarks.tools.scale
   
   .. automethod:: deap.benchmarks.tools.scale.scale

.. autofunction:: deap.benchmarks.tools.translate

   .. automethod:: deap.benchmarks.tools.translate.translate