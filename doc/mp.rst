===============
Multiprocessing
===============

The multiprocessing example shows how to use the :mod:`multiprocessing` module in order to enhance the computing power during the evolution. First the toolbox contains a method named :func:`~eap.map`, this method has the same function as the built-in :func:`map` function. In order to use the multiprocessing module into the built-in :mod:`~eap.algorithms`, the only thing to do is to replace the map operation by a parallel one. Then the difference between the `Multiprocessing One Max Example <http://deap.googlecode.com/hg/examples/mpga_onemax.py>`_ and the `Regular One Max Example <http://deap.googlecode.com/hg/examples/ga_onemax.py>`_ is the addition of these two lines ::

   # Process Pool of 4 workers
   pool = multiprocessing.Pool(processes=4)
   tools.register("map", pool.map)

.. note::
   The pickling of partial function is possible only since Python 2.7 (or 3.1), earlier version of Python may throw some strange errors when using partial function in the multiprocessing :func:`multiprocessing.Pool.map`. This may be avoided by creating local function outside of the toolbox (in Python version 2.6 and earlier).
   
.. note::
   The pickling of lambda function is not yet available in Python.