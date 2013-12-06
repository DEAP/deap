Benchmarking Against the Bests (BBOB)
=====================================

Once you've created your own algorithm, the structure of DEAP allows you to
benchmark it against the best algorithms very easily. The interface of the
`Black-Box Optimization Benchmark <http://coco.gforge.inria.fr/>`_ (BBOB) is
compatible with the toolbox. In fact, once your new algorithm is encapsulated in
a main function, there is almost nothing else to do on DEAP's side. This tutorial
will review the essential steps to bring everything to work with the very basic
:ref:`one-fifth`.

Preparing the Algorithm
-----------------------

The BBOB makes use of many continuous functions on which the algorithm will be
tested. These functions are given as an argument to the algorithm. The toolbox
shall thus register the evaluation in the main function.

The evaluation functions provided by BBOB return a fitness as a single value.
The first step is to put each fitness in its own tuple, as required by DEAP's
philosophy on single objective optimization. We will use a decorator for this.

.. literalinclude:: ../../../examples/bbob.py
   :pyobject: tupleize

The algorithm is encapsulated in a main function that receives four arguments:
the evaluation function, the dimensionality of the problem, the maximum number
of evaluations and the target value to reach. As stated earlier, the toolbox is
initialized in the main function with the :func:`update` function (described in
the example) and the evaluation function received, which is decorated by our
tuple-izer.

Then, the target fitness value is encapsulated in a :class:`FitnessMin` object
so that we can easily compare the individuals with it. The last step is to
define the algorithm, which is explained in the :ref:`one-fifth` example.

.. literalinclude:: ../../../examples/bbob.py
   :pyobject: main

Running the Benchmark
---------------------

Now that the algorithm is ready, it is time to run it under the BBOB. The
following code is taken from the BBOB example with added comments. The
:mod:`fgeneric` module provides a :class:`LoggingFunction`, which take care of
outputting all necessary data to compare the tested algorithm with the other
ones published and to be published.

This logger contains the current problem instance and provides the problem
target. Since it is responsible of logging each evaluation function call, it is
not even needed to save the best individual found by our algorithm (call to the
:func:`main` function). The single line that is related to the provided
algorithm in the call to the :func:`main` function.

.. literalinclude:: ../../../examples/bbob.py
   :lines: 26,27,28,90-137

Once these experiments are done, the data contained in the :file:`ouput`
directory can be used to build the results document. See the `BBOB
<http://coco.gforge.inria.fr/>`_ web site on how to build the document.

The complete example is available in the file :example:`bbob`.
