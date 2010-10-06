=========================
Using Multiple Processors
=========================

This section of the tutorial shows all the big work that is needed to paralellize operations in eap.

Multiprocessing Module
======================

This part of the tutorial shows all the work that is needed to use the :mod:`multiprocessing` module in EAP.

.. note::
   While Python 2.6 is required for the multiprocessing module, the pickling of partial function is possible only since Python 2.7 (or 3.1), earlier version of Python may throw some strange errors when using partial function in the multiprocessing :func:`multiprocessing.Pool.map`. This may be avoided by creating local function outside of the toolbox (in Python version 2.6).

.. note::
   The pickling of lambda function is not yet available in Python.

Evaluation
++++++++++

The multiprocessing example shows how to use the :mod:`multiprocessing` module in order to enhance the computing power during the evaluations. First the toolbox contains a method named :func:`~eap.map`, this method has the same function as the built-in :func:`map` function. In order to use the multiprocessing module into the built-in :mod:`~eap.algorithms`, the only thing to do is to replace the map operation by a parallel one. Then the difference between the `Multiprocessing One Max Example <http://deap.googlecode.com/hg/examples/mpga_onemax.py>`_ and the `Regular One Max Example <http://deap.googlecode.com/hg/examples/ga_onemax.py>`_ is the addition of these two lines ::

   # Process Pool of 4 workers
   pool = multiprocessing.Pool(processes=4)
   tools.register("map", pool.map)

Variation
+++++++++

The paralellization of the variation operators is not directly supported in the algorithms, although it is still possible. What one needs is to create its own algorithm (from one in the algorithm module for example) and change the desired lines in order to use the :meth:`~eap.toolbox.map` method from the toolbox. This may be achieved for example, for the crossover operation from the :func:`~eap.algorithms.eaSimple` algorithm by replacing the crossover part of the algorithms by ::
    
    parents1 = list()
    parents2 = list()
    to_replace = list()
    for i in range(1, len(offsprings), 2):
        if random.random() < cxpb:
            parents1.append(offsprings[i - 1])
            parents2.append(offsprings[i])
            to_replace.append(i - 1)
            to_replace.append(i)
    
    children = tools.map(tools.mate, (parents1, parents2))
    
    for i, child in zip(to_replace, children):
        del child.fitness.values
        offsprings[i] = child

Since the multiprocessing map does take a single iterable we must bundle/unbundle the parents, respectively by creating a tuple in the :func:`tools.map` function of the preceding code example and the following decorator on the crossover function. ::

    def unbundle(func):
        def wrapUnbundle(bundled):
            return func(*bundled)
        return wrapUnbundle
    
    tools.decorate("mate", unbundle)
