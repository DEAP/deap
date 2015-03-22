==================
Release Highlights
==================
Here is the list of changes made to DEAP for the current release.

API enhancements
++++++++++++++++

- algorithms: Every algorithm now return the final population and a logbook
  containing the evolution statistical data.
- base: Fitness objects are now hashable.
- base: Added a ``dominates`` function to the Fitness, which can be replaced.
  This function is now used in most multi-objective specific selection methods
  instead of ``isDominated``.
- base: Fitness - implementation of a ``__repr__`` method. (issue 20)
- examples: Removed prefix (ga, gp, pso, etc.) from examples filename.
- gp: Added ``pset`` to mutation operators that require it.
- gp: Replaced the :func:`~deap.gp.stringify` function by :func:`PrimitiveTree.__str__`. Use ``str`` or ``print`` on trees to read their code.
- gp: Added an explicit description of the error when there are no available
  primitive/terminal of a certain type.
- gp: Added symbolic regression benchmarks in ``benchmarks.gp``.
- gp: Removed the ephemeral generator.
- gp: Added a :func:`~deap.gp.PrimitiveTree.from_string` function to :class:`~deap.gp.PrimitiveTree`.
- gp: Added the possibility to name primitives added to a PrimitiveSet in :func:`~deap.gp.PrimitiveSet.addPrimitive`.
- gp: Added object oriented inheritance to strongly typed genetic programming.
- gp: :class:`~deap.gp.PrimitiveSetTyped` now requires real classes as type instead of string. See the :doc:`Spambase example <examples/gp_spambase>`.
- gp: Replaced :func:`~deap.gp.evaluate` and :func:`~deap.gp.lambdify` by a single function :func:`~deap.gp.compile`.
- gp: Replaced :func:`~deap.gp.lambdifyADF` by :func:`~deap.gp.compileADF`.
- gp: New :func:`~deap.gp.graph` function that returns a list of nodes, edges and a
  labels dictionnary that can then be feeded directly to networkx to
  draw the tree.
- gp: Renamed :func:`deap.gp.genRamped` as :func:`deap.gp.genHalfAndHalf`.
- gp: Merged :func:`~deap.gp.staticDepthLimit` and :func:`~deap.gp.staticSizeLimit` in a 
  single function :func:`~deap.gp.staticLimit` which takes a key function in argument than can
  be return the height, the size or whatever attribute the tree should be limited on.
- tools: Revised the :class:`~deap.tools.HallOfFame` to include only unique individuals.
- tools: Changed the way statistics are computed. See the
  :class:`~deap.tools.Statistics` and :class:`~deap.tools.MultiStatistics`
  documentation for more details and the tutorial :doc:`logging statistics <tutorials/basic/part3>` (issue 19).
- tools: Replaced the :class:`EvolutionLogger` by :class:`~deap.tools.Logbook`.
- tools: Removed :class:`~deap.tools.Checkpoint` class since it was more trivial to do simple
  checkpointing than using the class. The documentation now includes an
  example on how to do checkpointing without Checkpoint.
- tools: Reorganize the operators in submodule, tools now being a package.
- tools: Implementation of the logarithmic non-dominated sort by
  Fortin et al. (2013), available under the name :func:`~deap.tools.sortLogNondominated`.
- tools: Mutation operators can now take either a value or a sequence
  of values as long as the individual as parameters (low, up, sigma, etc.).
- tools: Removed DTM from the sources.
- tools: Removed the cTools module. It was not properly maintained and
  rarely used.
- tools: Renamed :func:`~deap.tools.cxTwoPoints` as :func:`~deap.tools.cxTwoPoint`
- tools: Renamed :func:`~deap.tools.cxESTwoPoints` as :func:`~deap.tools.cxESTwoPoint`
- tools: Bounds as well as some other attribute related parameters now accept iterables or
  values as argument in crossovers and mutations.


Documentation enhancements
++++++++++++++++++++++++++

- Major overhaul of the documentation structure.
- Tutorial are now decomposed in two categories: basic and advanced.
- New tutorial on :doc:`logging statistics <tutorials/basic/part3>`
- New tutorial on :doc:`checkpointing <tutorials/advanced/checkpoint>`
- New tutorial on :doc:`inheriting from Numpy <tutorials/advanced/numpy>`

Bug fixes
+++++++++

**Release 1.0.0**

- creator: Issue 23: error in creator when using unicode source.
- creator: create does not handle proper slicing of created classes inheriting
  from ``numpy.ndarray`` anymore. This was bug prone and extremely hard to maintain.
  Users are now requested to include ``numpy.copy()`` operation in their
  operators. A tutorial on inheriting from numpy is on its way.

**Release 1.0.1**:

- tools: issue #26: Operators with bounds do not work correctly when 
  bounds are provided as list instead of iterator. rev: `b172432515af`, `9d4718a8cf2a`.
- tools: add missing arguments to sortLogNondominated  (`k`, `first_front_only`). rev: `f60a6520b666`, `4de7df29dd0f`.
- gp: issue #32: :meth:`~deap.gp.PrimitiveTree.from_string` used incorrect argument order with STGP. rev: `58c1a0711e1f`.

**Release 1.0.2**:

- benchmarks: fix computation of DTLZ2, DTLZ3 and DTLZ4.
- cma 1+Lambda: fix the computation of the rank-one update.
- gp: replace the generate functions default value for the argument `type_` from `object` to `None`. 
  This removes the obligation to define the type_ argument for the individual generation function when doing STGP.
- gp: fix a bug with OOGP when calling addPrimitive and addTerminal in arbitrary order.
- gp: fix Ephemeral regeneration with mutEphemeral. rev: `ae46705`.
- gp: fix issue #35 - from_string had issues with OOGP.
- Fix issue #26: in four examples, files are opened but never closed.

