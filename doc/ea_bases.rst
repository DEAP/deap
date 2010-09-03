.. _ea-bases:

============================
Evolutionary Algorithm Bases
============================

.. automodule:: eap.base

.. _containers:

Container Types
===============

As of version 0.5.0, eap does not provide base types that wrap python base types, instead it is possible to create your own types that inherits from whatever type is more convenient or appropriate, for example, :class:`list`, :class:`array`, :class:`set`, :class:`dict`, etc. As most of those types are initialized using an iterable, the :mod:`~eap.creator` allows to create these objects using internal generators in order to produce objects with different content. See the :mod:`~eap.creator` module for more information.

.. autoclass:: eap.base.Tree([content])
   :members:

Fitness
=======

.. autoclass:: eap.base.Fitness
   :members:

Creator
=======

.. automodule:: eap.creator

.. autofunction:: eap.creator.create(name, base[, attribute[, ...]])

   For example, using ::
   
       creator("MyType", object, value=4, data=lambda: random.random())
       
   is the same as defining in the module :mod:`eap.creator` ::
   
       class MyType(object):
           value = 4
           def __init__(self):
               self.data = random.random()
   

Population, Individual and Other Structures
============================================

All application specific structures may be built using the :func:`~eap.creator.create` function and types defined in python or the :mod:`~eap.base` module. Here are some simple recipes to build very simple types.

Fitness
+++++++

As described earlier, the :class:`eap.base.Fitness` instantiate by default a minimizing fitness. This can be changed using the :mod:`~eap.creator` and its :func:`eap.creator.create` function. A maximizing fitness can be created using ::

    create("FitnessMax", base.Fitness, weights=(1.0,))


Individual
++++++++++

There is only one rule when building an individual, it **must** contain a :attr:`fitness` attribute. The following all produce valid individuals that are suited for most evolutionary algorithms.

Individual List
---------------

The individual list is suited for binary, integer, float and even funky individuals. It may contain any type and/or any type mix that is needed. The :class:`IndividualList` type is created with ::

    create("IndividualList", list, fitness=creator.FitnessMax)

and an individual of *size* 5 is instantiated with ::

    content = [random.random() for i in xrange(5)]
    ind = creator.IndividualList(content)

.. note::
   For individuals containing only a single numeric type, it may be more suited to use the :class:`array` base class, as the copy operation is way more efficient.

Individual Indices
------------------

The individual indices is almost the same as the individual list, except for its content. Here we will use the maximizing fitness describes earlier ::

    create("IndividualIndices", list, fitness=creator.FitnessMax)

and an individual indices of *size* 5 is instantiated with ::

    content = random.sample(xrange(5), 5)
    ind = creator.IndividualIndices(content)

Individual Tree
---------------

The individual tree is a bit harder to create. We first must define a primitive set and the operator we need in our post-fix trees. ::

    pset = gp.PrimitiveSet("MAIN", 1)
    pset.addPrimitive(operator.add, 2)
    pset.addPrimitive(operator.sub, 2)
    pset.addPrimitive(operator.mul, 2)

Then it is just as easy as other types, the tree class may be initialized from a iterable. The :mod:`~eap.gp` module contains some helper functions to build trees. For example, the :func:`~eap.gp.generate_full` will produce a full tree. ::

    creator.create("IndividualTree", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)
    ind = creator.IndividualTree(gp.generate_full(pset=pset, min=3, max=5))

Population
++++++++++

A population is usually a list of individuals or sub-populations, it is no more complicated to create than an individual. When using a :class:`~eap.toolbox.Toolbox`, it is often not necessary to create a class :class:`Population`, it is made here just to show how it would be created. ::

    create("Population", list)
    
A population of 10 individuals of indices is instanciated using ::

    ind_content = lambda: random.sample(xrange(5), 5)
    pop_content = [creator.IndividualIndices(ind_content()) for i in xrange(10)]
    pop = creator.Population(pop_content)
    
.. note::
   A deme (sub-population) is no more than a population, it is created the same way as a population (or any other list type).

.. seealso::
    
    The :ref:`First Steps of Evolution <first-steps>` shows how to combine the :mod:`~eap.creator` and the :mod:`~eap.toolbox` to initialize types.
