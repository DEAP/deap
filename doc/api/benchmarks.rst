==========
Benckmarks
==========

.. automodule:: deap.benchmarks

Continuous Optimization
=======================

.. autofunction:: deap.benchmarks.cigar

.. autofunction:: deap.benchmarks.plane

.. autofunction:: deap.benchmarks.sphere

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