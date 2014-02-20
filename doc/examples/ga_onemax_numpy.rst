============================
One Max Problem: Using Numpy
============================

The numpy version one max genetic algorithm example is very similar to one max
short example. The individual class is inherited from the :class:`numpy.ndarray`.

.. literalinclude:: /../examples/ga/onemax_numpy.py
   :lines: 18,26

The first major difference is the crossover function that implements
the copying mechanism mentionned in the :doc:`/tutorials/advanced/numpy` tutorial.

.. literalinclude:: /../examples/ga/onemax_numpy.py
   :pyobject: cxTwoPointCopy

This crossover function is added to the toolbox instead of the original
:func:`deap.tools.cxTwoPoint` crossover.

.. literalinclude:: /../examples/ga/onemax_numpy.py
   :lines: 67

The second major difference is the use of the *similar* function in the
:class:`~deap.tools.HallOfFame` that has to be set to a :func:`numpy.array_equal`
or :func:`numpy.allclose`

.. literalinclude:: /../examples/ga/onemax_numpy.py
   :lines: 80

The complete source code: :example:`ga/onemax_numpy`.