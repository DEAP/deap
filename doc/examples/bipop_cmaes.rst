.. _bipopcma-es:

================================================
Controlling the Stopping Criteria: BI-POP CMA-ES
================================================
A variant of the Covariance Matrix Adaptation Evolution Strategy (CMA-ES)
[Hansen2001]_ implies to control very specifically the termination criteria
in the generational loop. This can be achieved by writing the algorithm
partially invoking manually the :meth:`generate` and :meth:`update` inside a
loop with specific stop criteria. In fact, the BI-POP CMA-ES [Hansen2009]_
has 9 different stop criteria, which are used to control the independent
restarts, with different population sizes, of a standard CMA-ES.

As usual, the first thing to do is to create the types and as usual, we'll
need a minimizing fitness and an individual that is a :class:`list`.

.. literalinclude:: /code/examples/es/cmaes_bipop.py
   :lines: 34-35

The main function includes the setting of some parameters, namely the number
of increasing population restarts and the initial sigma value. Then, the
instanciation of the :class:`~deap.base.Toolbox` is done in the main function
because it will change with the restarts. Next are initialized the
:class:`~deap.tools.HallOfFame` and the :class:`~deap.tools.Statistics`
objects.

.. literalinclude:: /code/examples/es/cmaes_bipop.py
   :lines: 37-50

Then the first loop controlling the restart is set up. It encapsulates the
generational loop with its many stop criteria. The content of this last loop
is simply the generate-update loop as presented in the
:func:`deap.algorithms.eaGenerateUpdate` function.

.. literalinclude:: /code/examples/es/cmaes_bipop.py
   :lines: 65,101,103-110,113-120,124-126,149-188,191

Some variables have been omited for clarity, refer to the complete example for
more details [`source code <code/es/cmaes_bipop.py>`_].

.. [Hansen2001] Hansen and Ostermeier, 2001. Completely Derandomized
   Self-Adaptation in Evolution Strategies. *Evolutionary Computation*
.. [Hansen2009] Hansen, 2009. Benchmarking a BI-Population CMA-ES on the 
   BBOB-2009 Function Testbed. *GECCO'09*