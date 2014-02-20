.. _short-ga-onemax:

===============================
One Max Problem: Short Version
===============================

The short one max genetic algorithm example is very similar to one max
example. The only difference is that it makes use of the
:mod:`~deap.algorithms` module that implements some basic evolutionary
algorithms. The initialization are the same so we will skip this phase. The
algorithms impemented use specific functions from the toolbox, in this case
:func:`evaluate`, :func:`mate`, :func:`mutate` and :func:`~deap.Toolbox.select`
must be registered. 

.. literalinclude:: /../examples/ga/onemax_short.py
   :lines: 41-44

The toolbox is then passed to the algorithm and the algorithm uses the
registered function. 

.. literalinclude:: /../examples/ga/onemax_short.py
   :lines: 46, 49-58

The short GA One max example makes use of a
:class:`~deap.tools.HallOfFame` in order to keep track of the best
individual to appear in the evolution (it keeps it even in the case it
extinguishes), and a :class:`~deap.tools.Statistics` object to compile
the population statistics during the evolution.

Every algorithms from the :mod:`~deap.algorithms` module can take
these objects. Finally, the *verbose* keyword indicate wheter we
want the algorithm to output the results after each generation or
not.

The complete source code: :example:`ga/onemax_short`.
