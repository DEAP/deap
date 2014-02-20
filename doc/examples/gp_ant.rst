.. _artificial-ant:
    
======================
Artificial Ant Problem
======================

The Artificial Ant problem is a more sophisticated yet classical GP problem,
in which the evolved individuals have to control an artificial ant so that it
can eat all the food located in a given environment. This example shows how
DEAP can easily deal with more complex problems, including an intricate
system of functions and resources (including a small simulator).

For more information about this problem, see :ref:`refPapersAnt`.

Primitives set used
===================

We use the standard primitives set for the Artificial Ant problem :
    
.. literalinclude:: /../examples/gp/ant.py
   :lines: 150-156

- ``if_food_ahead`` is a primitive which executes its first argument if there
  is food in front of the ant; else, it executes its second argument.
- :func:`prog2` and :func:`prog3` are the equivalent of the lisp PROGN2 and
  PROGN3 functions. They execute their children in order, from the first to
  the last. For instance, prog2 will first execute its first argument, then
  its second.
- :func:`move_forward` makes the artificial ant move one front. This is a
  terminal.
- :func:`turn_right` and :func:`turn_left` makes the artificial ant turning
  clockwise and counter-clockwise, without changing its position. Those are
  also terminals.

.. note::
    There is no external input as in symbolic regression or parity.

Although those functions are obviously not already built-in in Python, it is
very easy to define them :

.. literalinclude:: /../examples/gp/ant.py
   :lines: 62-75, 122-123

Partial functions are a powerful feature of Python which allow to create
functions on the fly. For more detailed information, please refer to the
Python documentation of :func:`functools.partial`.


Evaluation function
===================

The evaluation function use an instance of a simulator class to evaluate the
individual. Each individual is given 600 moves on the simulator map (obtained
from an external file). The fitness of each individual corresponds to the
number of pieces of food picked up. In this example, we are using a classical
trail, the *Santa Fe trail*, in which there is 89 pieces of food. Therefore,
a perfect individual would achieve a fitness of 89.

.. literalinclude:: /../examples/gp/ant.py
   :pyobject: evalArtificialAnt

Where `ant` is the instance of the simulator used. The
:func:`~deap.gp.evaluate` function is a convenience one provided by DEAP and
returning an executable Python program from a GP individual and its
primitives function set.

Complete example
================

Except for the simulator code (about 75 lines), the code does not
fundamentally differ from the :ref:`Symbolic Regression example <symbreg>`.
Note that as the problem is harder, improving the selection pressure by
increasing the size of the tournament to 7 allows to achieve better
performance.

The complete :example:`gp/ant`

.. _refPapersAnt:

Reference
=========

*John R. Koza, "Genetic Programming I: On the Programming of Computers by
Means of Natural Selection", MIT Press, 1992, pages 147-161.*
