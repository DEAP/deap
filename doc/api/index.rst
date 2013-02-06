API
---
The API of DEAP is built around a clean and lean core composed of two simple
structures: a :mod:`~deap.creator` and :class:`~deap.base.Toolbox`. The former
allows creation of classes via inheritance and composition and
the latter contains the tools that are required by the evolutionary algorithm.
The core functionalities of DEAP are levered by several peripheral modules.
The :mod:`~deap.tools` module provides a bunch of operator that are commonly
used in evolutionary computation such as initialization, mutation, crossover
and selection functions. It also contains all sort of tools to gather
information about the evolution such as statistics on almost every thing,
genealogy of the produced individuals, hall-of-fame of the best individuals
seen, and checkpoints allowing to restart an evolution from its last state.
The :mod:`~deap.algorithms` module contains five of the most frequently used
algorithms in EC: generational, steady-state, :math:`(\mu\ ,\ \lambda)`,
:math:`(\mu+\lambda)`, and CMA-ES. These are readily usable for the most
common population layouts. Specific genetic programming tools are provided in
the :mod:`~deap.gp` module. A complete and efficient (and stand alone)
parallelization module, base on MPI, providing some very useful parallel
method is provided in the :mod:`~deap.dtm` module. Finally, common benchmark
functions are readily implemented in the :mod:`~deap.benchmarks`.

.. toctree::
	:maxdepth: 2
	:numbered:
   
	core
	tools
	algo
	gp
	dtm
        benchmarks
