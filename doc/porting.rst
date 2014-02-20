=============
Porting Guide
=============

DEAP development's high velocity and our refusal to be at the mercy of
backward compatibility can sometime induce minor headaches to our users.
This concise guide should help you port your code from the latest version minus 
0.1 to the current version.

General
=======

#. The algorithms from the :mod:`~deap.gp.algorithms` module now return a tuple of 2-elements : the population and a :class:`~deap.tools.Logbook`.
#. Replace every call to DTM by calls to  `SCOOP <http://scoop.googlecode.com>`_.
#. Statistics and logging of data are accomplished by two distinct objects: :class:`~deap.tools.Statistics` and :class:`~deap.tools.Logbook`. Read the tutorial on :doc:`logging statistics <tutorials/basic/part3>`. 
#. Replace :class:`~deap.tools.EvolutionLogger` by :class:`~deap.tools.Logbook`.
#. Replace usage of :func:`tools.mean`, :func:`tools.var`, :func:`tools.std`, and :func:`tools.median` by their Numpy equivalent.
#. If the fitness has multiple objectives, add the keyword argument ``axis=0`` when registering statistical function.

Genetic Algorithms (GA)
=======================

#. Replace every call to the function :func:`~deap.tools.cxTwoPoints` by a call to :func:`~deap.tools.cxTwoPoint`.
#. Remove any import of cTools. If you need a faster implementation of the non-dominated sort, use :func:`~deap.tools.sortLogNondominated`.
#. When inheriting from Numpy, you must manually copy the slices and compare individuals with numpy comparators. See the :doc:`tutorials/advanced/numpy` tutorial.

Genetic Programming (GP)
========================

#. Specify a ``name`` as the first argument of every call to :func:`~deap.gp.PrimitiveSet.addEphemeralConstant`. 
#. Replace every call to :func:`~deap.gp.lambdify` and :func:`~deap.gp.evaluate` by a call to :func:`~deap.gp.compile`.
#. Remove the pset attribute from every :func:`~deap.creator.create` call when creating a primitive tree class.
#. In the toolbox, register the primitive set as the ``pset`` argument of the following mutation operator: :func:`~deap.gp.mutUniform`, :func:`~deap.gp.mutNodeReplacement` and :func:`~deap.gp.mutInsert`.
#. Replace every call to the function :func:`~deap.gp.genRamped` by a call to :func:`~deap.gp.genHalfAndHalf`.
#. Replace every call to :func:`~deap.gp.stringify` by a call to :func:`str` or remove the call completely.
#. Replace every call to :func:`~deap.gp.lambdifyADF` by a call to :func:`~deap.gp.compileADF`.
#. Replace the decorators :func:`~deap.gp.staticDepthLimit` and :func:`~deap.gp.staticSizeLimit` by :func:`~deap.gp.staticLimit`. To specify a limit on either depth, size or any other attribute, it is now required to specify a `key` function. See :func:`~deap.gp.staticLimit` documentation for more information.

Strongly Typed Genetic Programming (STGP)
-----------------------------------------

#. :class:`~deap.gp.PrimitiveSetTyped` method now requires type arguments to be defined as classes instead of string, for example ``float`` instead of ``"float"``.

Evolution Strategy (ES)
=======================

#. Replace every call to the function :func:`~deap.tools.cxESTwoPoints` by a call to :func:`~deap.tools.cxESTwoPoint`.


Still having problem?
=====================

We have overlooked something and your code is still not working?
No problem, contact us on the deap users list at 
`<http://groups.google.com/group/deap-users>`_ and we will get you out
of trouble in no time.