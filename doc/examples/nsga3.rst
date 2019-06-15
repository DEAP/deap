.. _nsga-3:

======================================================
Non-dominated Sorting Genetic Algorithm III (NSGA-III)
======================================================
The Non-dominated Sorting Genetic Algorithm III (NSGA-III) [Deb2014]_
is implemented in the :func:`deap.tools.selNSGA3` function. This example
shows how it can be used in DEAP for many objective optimization.

Problem Definition
------------------
First we need to define the problem we want to work on. We will use
the first problem tested in the paper, 3 objectives DTLZ2 with ``k = 10``
and ``p = 12``. We will use `pymop <https://github.com/msu-coinlab/pymop>`_
for problem implementation as it provides the exact Pareto front that we
will use later for computing the performance of the algorithm.

.. literalinclude:: /../examples/ga/nsga3.py
   :start-after: # Problem definition
   :end-before: ##

Algorithm Parameters
--------------------
Then we define the various parameters for the algorithm, including the
population size set to the first multiple of 4 greater than H, the
number of generations and variation probabilities.

.. literalinclude:: /../examples/ga/nsga3.py
   :start-after: # Algorithm parameters
   :end-before: ##

Classes and Tools
-----------------
Next, NSGA-III selection requires a reference point set. The reference point
set serves to guide the evolution into creating a uniform Pareto front in
the objective space.

.. literalinclude:: /../examples/ga/nsga3.py
   :start-after: # Create uniform reference point
   :lines: 1

The next figure shows an example of reference point set with ``p = 12``.
The cross represents the the utopian point (0, 0, 0).

.. plot:: code/examples/nsga3_ref_points.py

As in any DEAP program, we need to populate the creator with the type
of individual we require for our optimization. In this case we will use
a basic list genotype and minimization fitness.

.. literalinclude:: /../examples/ga/nsga3.py
   :start-after: # Create classes
   :end-before: ##

Moreover, we need to populate the evolutionary toolbox with initialization,
variation and selection operators. Note how we provide the reference point
set to the NSGA-III selection scheme.

.. literalinclude:: /../examples/ga/nsga3.py
   :start-after: # Toolbox initialization
   :end-before: ##

Evolution
---------
The main part of the evolution is mostly similar to any other
DEAP example. The algorithm used is close to the
:func:`~deap.algorithms.eaSimple` algorithm as crossover and mutation are
applied to every individual (see variation probabilities above). However,
the selection is made from the parent and offspring populations instead
of completely replacing the parents with the offspring.

.. literalinclude:: /../examples/ga/nsga3.py
   :pyobject: main

Finally, we can have a look at the final population

.. image:: /_images/nsga3.png
   :align: center

Higher Dimensional Objective Space
----------------------------------
NSGA-III requires a reference point set that depends on the number
of objective. This point set can become quite big for even relatively
low dimensional objective space. For example, a 15 dimensional
objective space with a uniform reference point set with ``p = 4``
would have 3060 points. To avoid this situation and reduce the
algorithms runtime [Deb2014]_ suggest to combine reference point
set with lower p value. To do this in DEAP, we can combine multiple
uniform point set using:

.. literalinclude:: ../code/examples/nsga3_ref_points_combined.py
   :start-after: # reference points
   :end-before: ##

This would give the following reference point set with two underlying
uniform distribution: one at full scale, and the other at half scale.

.. plot:: code/examples/nsga3_ref_points_combined_plot.py



Conclusion
----------
That's it for the NSGA-III algorithm using DEAP, now you can leverage
the power of many-objective optimization with DEAP. If you're interrested,
you can copy the `example <https://github.com/DEAP/deap/blob/nsga-3/examples/ga/nsga3.py>`_
change the evaluation function and try applying it to your own problem.

.. [Deb2014] Deb, K., & Jain, H. (2014). An Evolutionary Many-Objective Optimization
   Algorithm Using Reference-Point-Based Nondominated Sorting Approach,
   Part I: Solving Problems With Box Constraints. IEEE Transactions on
   Evolutionary Computation, 18(4), 577-601. doi:10.1109/TEVC.2013.2281535.
