.. _multiplexer:
    
==========================
GP Multiplexer 3-8 problem
==========================

The multiplexer problem is another extensively used GP problem. Basically, it trains a program to reproduce the behavior of an electronic `multiplexer <http://en.wikipedia.org/wiki/Multiplexer>`_ (mux). Usually, a 3-8 multiplexer is used (3 address entries, from A0 to A2, and 8 data entries, from D0 to D7), but virtually any size of multiplexer can be used.

This problem was first defined by Koza (see :ref:`refPapersMux`).

Primitives set used
===================

The primitive set is almost the same as the set used in :ref:`Parity <parity>`. Three Boolean operators (and, or and not), imported from :mod:`operator`, and a specific if-then-else primitive, which return either its second or third argument depending on the value of the first one. ::

    pset = gp.PrimitiveSet("MAIN", MUX_TOTAL_LINES, "IN")
    pset.addPrimitive(operator.and_, 2)
    pset.addPrimitive(operator.or_, 2)
    pset.addPrimitive(operator.not_, 1)
    pset.addPrimitive(if_then_else, 3)
    pset.addTerminal(1)
    pset.addTerminal(0)

As usual, we also add two terminals, a Boolean true and a Boolean false.

Evaluation function
===================

To speed up the evaluation, the computation of the input/output pairs is done at start up, instead of at each evaluation call. This pre-computation also allows to easily tune the multiplexer size, by changing the value of *MUX_SELECT_LINES*. ::

    MUX_SELECT_LINES = 3
    MUX_IN_LINES = 2 ** MUX_SELECT_LINES
    MUX_TOTAL_LINES = MUX_SELECT_LINES + MUX_IN_LINES

    # input : [A0 A1 A2 D0 D1 D2 D3 D4 D5 D6 D7] for a 8-3 mux
    inputs = [[0] * MUX_TOTAL_LINES for i in range(2 ** MUX_TOTAL_LINES)]
    outputs = [None] * (2 ** MUX_TOTAL_LINES)

    for i in range(2 ** MUX_TOTAL_LINES):
        value = i
        divisor = 2 ** MUX_TOTAL_LINES
        # Fill the input bits
        for j in range(MUX_TOTAL_LINES):
            divisor /= 2
            if value >= divisor:
                inputs[i][j] = 1
                value -= divisor
        
        # Determine the corresponding output
        indexOutput = MUX_SELECT_LINES
        for j, k in enumerate(inputs[i][:MUX_SELECT_LINES]):
            if k:   indexOutput += 2 ** j
        outputs[i] = inputs[i][indexOutput]

After that, the evaluation function is trivial, as we have both inputs and output values. The fitness is then the number of well predicted outputs over the 2048 cases (for a 3-8 multiplexer). ::

    def evalMultiplexer(individual):
        func = tools.lambdify(expr=individual)
        good = sum((func(*(inputs[i])) == outputs[i] for i in range(2 ** MUX_TOTAL_LINES)))
        return good,

Complete Example
================

.. literalinclude:: ../examples/gp_multiplexer.py
    :lines: 20-


.. _refPapersMux:

Reference
=========

*John R. Koza, "Genetic Programming I: On the Programming of Computers by Means of Natural Selection", MIT Press, 1992, pages 170-187.*
