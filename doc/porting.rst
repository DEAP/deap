Porting Guide
=============

DEAP development's high velocity and our refusal to be at the mercy of
backward compatibility can sometime induce minor headaches to our users.
This concise guide should help you port your code from the latest version minus 
0.1 to the current version.

General
-------

#. The algorithms from the :mod:`~deap.gp.algorithms` module now return a tuple of 2-elements : the population and a :class:`~deap.tools.Logbook`.
#. Replace every call to DTM by calls to  `SCOOP <http://scoop.googlecode.com>`_.
#. Statistics and logging of data are accomplished by two distinct objects: :class:`~deap.tools.Statistics` and :class:`~deap.tools.Logbook`. Read the tutorial on :doc:`logging statistics <tutorials/basic/part3>`.

Genetic Algorithms (GA)
-----------------------

#. Replace every call to the function :func:`~deap.tools.cxTwoPoints` by a call to :func:`~deap.tools.cxTwoPoint`.
#. Remove any import of cTools. If you need a faster implementation of the non-dominated sort, use :func:`~deap.tools.sortLogNondominated`.
#. When inheriting from Numpy, you must manually copy the slices and compare individuals with numpy comparators. See the :doc:`tutorials/advanced/numpy` tutorial.

Genetic Programming (GP)
------------------------

#. Remove the pset attribute from every :func:`~deap.creator.create` call when creating a primitive tree class.
#. In the toolbox, register the primitive set as the ``pset`` argument of the following mutation operator: :func:`~deap.gp.mutUniform`, :func:`~deap.gp.mutNodeReplacement` and :func:`~deap.gp.mutInsert`.
#. Replace every call to :func:`~deap.gp.lambdify` and :func:`~deap.gp.evaluate` by a call to :func:`~deap.gp.compile`.
#. Replace every call to the function :func:`~deap.gp.genRamped` by a call to :func:`~deap.gp.genHalfAndHalf`.
#. Replace every call to :func:`~deap.gp.lambdifyADF` by a call to :func:`~deap.gp.compileADF`.
#. Replace every call to :func:`~deap.gp.stringify` by a call to :func:`str` or remove the call completely.


Evolution Strategy (ES)
-----------------------

#. Replace every call to the function :func:`~deap.tools.cxESTwoPoints` by a call to :func:`~deap.tools.cxESTwoPoint`.


Still having problem?
---------------------

We have overlooked something and your code is still not working?
No problem, contact us on the deap users list at 
`<http://groups.google.com/group/deap-users>`_ and we will get you out
of trouble in no time.