.. _short-ga-onemax:

===============================
One Max Problem: Short Version
===============================

The short One Max genetic algorithm example is very similar to the full one
:ref:`-ga-onemax`. The only difference is that it makes use of the
:mod:`~deap.algorithms` module which implements some basic evolutionary
algorithms. The initializations are almost the same. We only have to import
some additional packages and modules.

.. literalinclude:: /../examples/ga/onemax_short.py
   :lines: 16,19-21
	   
In order to use the evolution functions implemented in :mod:`~deap.algorithms`,
we have to register some functions from the :mod:`~deap.tools` module:
:func:`evaluate`, :func:`mate`, :func:`mutate`, and :func:`~deap.Toolbox.select`.

.. literalinclude:: /../examples/ga/onemax_short.py
   :lines: 41-44

The toolbox is then passed to the algorithm and via ``stats`` it uses the
registered functions. 

.. literalinclude:: /../examples/ga/onemax_short.py
   :lines: 46, 49-58

The short GA One max example makes use of a
:class:`~deap.tools.HallOfFame` in order to keep track of the best
individual to appear in the evolution (it keeps it even in the case of
extinction), and a :class:`~deap.tools.Statistics` object to compile
the population statistics during the evolution.

Every algorithm in the :mod:`~deap.algorithms` module can handle
these objects. Finally, the *verbose* keyword indicates whether we
want the algorithm to output the results after each generation or
not.

The complete source code: :example:`ga/onemax_short`.
