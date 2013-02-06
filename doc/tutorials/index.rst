Tutorial
--------
Although this tutorial doesn't make reference directly to the complete API of
the framework, we think it is the place to start to understand the principles
of DEAP. The core of the architecture is based on the :mod:`~deap.creator` and
the :class:`~deap.base.Toolbox`. Their usage to create types
is shown in the first part of this tutorial. Then, a next step is taken in the
direction of building generic algorithms by showing how to use the different
tools present in the framework. Finally, we conclude on how those algorithms
can be made parallel with minimal changes to the overall code (generally,
adding a single line of code will do the job).

.. toctree::
	:maxdepth: 2
	:numbered:
   
	start
	types
	next_step
	gp
	speedup
	distribution
	benchmarking
