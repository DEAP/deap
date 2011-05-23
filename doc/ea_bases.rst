.. _ea-bases:

============================
Evolutionary Algorithm Bases
============================

.. automodule:: deap.base

.. _containers:

Container Types
===============

.. autoclass:: deap.base.Tree([content])
   :members:

Fitness
=======

.. autoclass:: deap.base.Fitness([values])
   :members:

Creator
=======

.. automodule:: deap.creator

.. autofunction:: deap.creator.create(name, base[, attribute[, ...]])
   

Population, Individual and Other Structures
============================================

All application specific structures may be built using the
:func:`~deap.creator.create` function and types defined in the standard python 
library or the :mod:`~deap.base` module. Here are some simple recipes to build 
very simple types.

Fitness
+++++++

As described earlier, the :class:`~deap.base.Fitness` class is practically 
virtual and cannot be used directly as no weights are defined. In order to 
create a valid Fitness object one have to add the proper 
:attr:`~deap.base.Fitness.weights` attribute to the class object. This last 
step is done using the :func:`~deap.creator.create` function with an added
``weights`` argument. The following block of code does create a maximizing 
fitness class named :class:`FitnessMax`.
::

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))

This newly created class can be accessed via the creator module. An instance 
of the class can be created as in the following.
::

    fit = creator.FitnessMax()

Individual
++++++++++

There is only one rule when building an individual, it **must** contain a
:attr:`fitness` attribute. The following all produce valid individuals that
are suited for most evolutionary algorithms.

Individual List
---------------

The individual list is suited for binary, integer, float and even funky
individuals. It may contain any type and/or any type mix that is needed as it
is based on the Python standard library type :class:`list`. The
:class:`IndividualList` type is created with ::

    creator.create("IndividualList", list, fitness=creator.FitnessMax)

The last code block created an :class:`IndividualList` class in the creator 
module as seen for the fitness. This class inherits the :class:`list` 
constructor, thus, it is initialized from an iterable. The following block of 
code builds an initialized :class:`IndividualList` from a pre-allocated 
content.
::

    content = [random.random() for i in xrange(5)]
    ind = creator.IndividualList(content)

.. note::
   For individuals containing only a single numeric type, it may be more
   suited to use the :class:`array.array` base class, as the copy operation is
   way more efficient.

Individual Indices
------------------

The individual indices is almost the same as the individual list, except for
its content. Here we will use the maximizing fitness describes earlier 
::

    creator.create("IndividualIndices", list, fitness=creator.FitnessMax)

and an :class:`IndividualIndices` of containing numbers in 
:math:`\mathit{ind}_i \in \{1, \ldots, 5\}, \mathit{ind}_i \neq 
\mathit{ind}_j, \forall i, j` is instantiated with 
::

    content = random.sample(xrange(5), 5)
    ind = creator.IndividualIndices(content)

Individual Tree
---------------

The individual tree is a bit harder to create. We first must define a
primitive set and the operator we need in our trees. ::

    pset = gp.PrimitiveSet("MAIN", 1)
    pset.addPrimitive(operator.add, 2)
    pset.addPrimitive(operator.sub, 2)
    pset.addPrimitive(operator.mul, 2)

Then it is just as easy as other types, the tree class may be initialized from
a iterable. The :mod:`~deap.gp` module contains some helper functions to build
trees. For example, the :func:`~deap.gp.generate_full` will produce a full
tree. ::

    creator.create("IndividualTree", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)
    ind = creator.IndividualTree(gp.generate_full(pset=pset, min=3, max=5))

Population
++++++++++

A population is usually a list of individuals or sub-populations, it is no
more complicated to create than an individual. When using a
:class:`~deap.toolbox.Toolbox`, it is often not necessary to create a class
:class:`Population`, it is made here just to show how it would be created. ::

    create("Population", list)
    
A population of 10 individuals of indices is instanciated using ::

    ind_content = lambda: random.sample(xrange(5), 5)
    pop_content = [creator.IndividualIndices(ind_content()) for i in xrange(10)]
    pop = creator.Population(pop_content)
    
.. note::
   A deme (sub-population) is no more than a population, it is created the
   same way as a population (or any other list type).

.. seealso::
    
    The :ref:`First Steps of Evolution <first-steps>` shows how to combine the
    :mod:`~deap.creator` and the :mod:`~deap.toolbox` to initialize types.
