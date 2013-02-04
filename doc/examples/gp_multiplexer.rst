.. _mux:
    
=======================
Multiplexer 3-8 Problem
=======================

The multiplexer problem is another extensively used GP problem. Basically, it trains a program to reproduce the behavior of an electronic `multiplexer <http://en.wikipedia.org/wiki/Multiplexer>`_ (mux). Usually, a 3-8 multiplexer is used (3 address entries, from A0 to A2, and 8 data entries, from D0 to D7), but virtually any size of multiplexer can be used.

This problem was first defined by Koza (see :ref:`refPapersMux`).

Primitives set used
===================

The primitive set is almost the same as the set used in :ref:`Parity <parity>`. Three Boolean operators (and, or and not), imported from :mod:`operator`, and a specific if-then-else primitive, which return either its second or third argument depending on the value of the first one.

.. literalinclude:: /code/examples/gp/gp_multiplexer.py
   :lines: 54-60

As usual, we also add two terminals, a Boolean true and a Boolean false.

Evaluation function
===================

To speed up the evaluation, the computation of the input/output pairs is done at start up, instead of at each evaluation call. This pre-computation also allows to easily tune the multiplexer size, by changing the value of *MUX_SELECT_LINES*. 

.. literalinclude:: /code/examples/gp/gp_multiplexer.py
   :lines: 30-52


After that, the evaluation function is trivial, as we have both inputs and output values. The fitness is then the number of well predicted outputs over the 2048 cases (for a 3-8 multiplexer). 

.. literalinclude:: /code/examples/gp/gp_multiplexer.py
   :pyobject: evalMultiplexer

The complete example: [`source code <code/gp/gp_multiplexer.py>`_]

.. _refPapersMux:

Reference
=========

*John R. Koza, "Genetic Programming I: On the Programming of Computers by Means of Natural Selection", MIT Press, 1992, pages 170-187.*
