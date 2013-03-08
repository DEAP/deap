.. _distribution-deap:

Using Multiple Processors
=========================

This section of the tutorial shows all the work that is needed to
distribute operations in deap. Distribution relies on serialization of objects
and serialization is usually done by pickling, thus all objects that are
distributed (functions and arguments, e.g. individuals and parameters) must be
pickleable. This means modifications made to an object on a distant processing
unit will not be made available to the other processing units (including the
master one) if it is not explicitly communicated through function arguments
and return values.

Scalable Concurent Operations in Python (SCOOP)
-----------------------------------------------

`SCOOP <http://scoop.googlecode.com>`_ is a distributed task module allowing
concurrent parallel programming on various environments, from heterogeneous
grids  to supercomputers. It has an interface similar to the
:mod:`concurrent.futures`  module introduced in Python 3.2. Its two simple
functions :func:`~scoop.futures.submit`  and :func:`~scoop.futures.map` allow to
distribute computation efficiently and easily over a grid of computers.

In the :ref:`last section <using-tools>` a complete algorithm was exposed with
the :func:`toolbox.map` left to the default :func:`map`. In order to
distribute the evaluations, we will replace this map by the one from SCOOP.
::

    from scoop import futures

    toolbox.register("map", futures.map)

Once this line is added, your program absolutly needs to be run from a
:func:`main` function as mentionned in the scoop documentation. To run your
program, use scoop as the main module.

.. code-block:: bash

    $ python -m scoop your_program.py

That is it, your program has been run in parallel on all available processors.


Distributed Task Manager
------------------------
.. deprecated:: 0.9
   Use `SCOOP`_ instead, it is a fork of DTM and
   developped by the same group.

Distributing tasks on multiple computers is taken care of by the distributed
task manager module :mod:`~deap.dtm`. Its API similar to the multiprocessing
module allows it to be very easy to use. In the :ref:`last section
<using-tools>` a complete algorithm was exposed with the :func:`toolbox.map`
left to the default :func:`map`. In order to distribute the evaluations,
simply replace this map with the one provided by the dtm module
and tell to dtm which function is the main program here it is the :func:`main`
function.
::

    from deap import dtm
    
    toolbox.register("map", dtm.map)
    
    def main():
        # My evolutionary algorithm
        pass
    
    if __name__ == "__main__":
        dtm.start(main)

That's it. The map operation contained in the toolbox will now be distributed.
The next time you run the algorithm, it will run on the number of cores
specified to the ``mpirun`` command used to run the python script. The usual
bash command to use dtm will be :

.. code-block:: bash

    $ mpirun [options] python my_script.py

Multiprocessing Module
----------------------
Using the :mod:`multiprocessing` module is exactly similar to using the
distributed task manager. Again in the
toolbox, replace the appropriate function by the distributed one.
::

    import multiprocessing
    
    pool = multiprocessing.Pool()
    toolbox.register("map", pool.map)
    
    # Continue on with the evolutionary algorithm

.. warning::
   As stated in the :mod:`multiprocessing` guidelines, under Windows, a
   process pool must be protected in a ``if __name__ == "__main__"`` section
   because of the way processes are initialized.

.. note::
   While Python 2.6 is required for the multiprocessing module, the pickling
   of partial function is possible only since Python 2.7 (or 3.1), earlier
   version of Python may throw some strange errors when using partial function
   in the multiprocessing :func:`multiprocessing.Pool.map`. This may be
   avoided by creating local function outside of the toolbox (in Python
   version 2.6).

.. note::
   The pickling of lambda function is not yet available in Python.


.. Parallel Evaluation
.. -------------------
.. The multiprocessing example shows how to use the :mod:`multiprocessing` module
.. in order to enhance the computing power during the evaluations. First the
.. toolbox contains a method named :func:`~deap.map`, this method has the same
.. function as the built-in :func:`map` function. In order to use the
.. multiprocessing module into the built-in :mod:`~deap.algorithms`, the only
.. thing to do is to replace the map operation by a parallel one. Then the
.. difference between the `Multiprocessing One Max Example
.. <http://deap.googlecode.com/hg/examples/mpga_onemax.py>`_ and the `Regular One
.. Max Example <http://deap.googlecode.com/hg/examples/ga_onemax.py>`_ is the
.. addition of these two lines 
.. ::
.. 
..    # Process Pool of 4 workers
..    pool = multiprocessing.Pool(processes=4)
..    tools.register("map", pool.map)
.. 
.. Parallel Variation
.. ------------------
.. 
.. The paralellization of the variation operators is not directly supported in
.. the algorithms, although it is still possible. What one needs is to create its
.. own algorithm (from one in the algorithm module for example) and change the
.. desired lines in order to use the :meth:`~deap.toolbox.map` method from the
.. toolbox. This may be achieved for example, for the crossover operation from
.. the :func:`~deap.algorithms.eaSimple` algorithm by replacing the crossover part
.. of the algorithms by 
.. ::
..     
..     parents1 = list()
..     parents2 = list()
..     to_replace = list()
..     for i in range(1, len(offspring), 2):
..         if random.random() < cxpb:
..             parents1.append(offspring[i - 1])
..             parents2.append(offspring[i])
..             to_replace.append(i - 1)
..             to_replace.append(i)
..     
..     children = tools.map(tools.mate, (parents1, parents2))
..     
..     for i, child in zip(to_replace, children):
..         del child.fitness.values
..         offspring[i] = child
.. 
.. Since the multiprocessing map does take a single iterable we must
.. bundle/unbundle the parents, respectively by creating a tuple in the
.. :func:`tools.map` function of the preceding code example and the following
.. decorator on the crossover function.
.. ::
.. 
..     def unbundle(func):
..         def wrapUnbundle(bundled):
..             return func(*bundled)
..         return wrapUnbundle
..     
..     tools.decorate("mate", unbundle)
