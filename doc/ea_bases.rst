.. _ea-bases:

============================
Evolutionary Algorithm Bases
============================

.. automodule:: eap.base

.. _containers:

Container Types
===============

.. autoclass:: eap.base.List([size, content])
    
   The most classic way to initialize a List is to provide a :data:`lambda` function using a random method, for instance, ::
    
       print List(size=3, content=lambda: random.choice((True, False)))
       [False, False, True]
    
   A similar way is to provide the *content* argument with a class. For example, lets build a simple :class:`MyTuple` class that initialize a tuple of boolean and integer in its member values ::
    
       class MyTuple(object):
           calls = 0
           def __init__(self):
               self.values = bool(self.calls), calls
               self.__class__.calls += 1
           def __repr__(self):
               return repr(self.values)
    
   Initializing a list of 3 :class:`MyTuples` is done by ::
    
       print List(size=3, content=MyTuple)
       [(False, 0), (True, 1), (True, 2)]
        
   The same result may be obtained by providing an iterable to the List's *content*, in that case, no *size* is needed since the size will be that same as the iterable provided. ::
    
       print List(content=[MyTuple(), MyTuple(), MyTuple()])
       [(False, 0), (True, 1), (True, 2)]
        
   The same thing may be achieved by the using a generator function. First, the generator must be defined ::
    
       def myGenerator(size):
           for i in xrange(size):
               yield MyTuple()
           raise StopIteration
            
   Then, it must be initialized and passed to List's *content* ::
    
           print List(content=myGenerator(size=3))
           [(False, 0), (True, 1), (True, 2)]

.. autoclass:: eap.base.Array(typecode[, size, content])

.. autoclass:: eap.base.Indices(size)

.. autoclass:: eap.base.Tree([content])

Fitness
=======

.. autoclass:: eap.base.Fitness
   :members:

The Creator
===========

.. automodule:: eap.creator

.. autofunction:: eap.creator.create(name, bases[, dict])

   For example, using ::
   
       creator("MyType", (object,), {"value" : 4, "data" : lambda: random.random()})
       
   is the same as defining in the module :mod:`eap.creator` ::
   
       class MyType(object):
           value = 4
           def __init__(self):
               self.data = random.random()
   

Population, Individual and Other Structures
============================================

All application specific structures may be built using the :func:`~eap.creator.create` function and types defined in the :mod:`~eap.base` module. Here are some simple receipies to build very simple types.

Fitness
+++++++

As described earlier, the :class:`eap.base.Fitness` instanciate by default a minimizing fitness. This can be changed using the :mod:`~eap.creator` and its :func:`eap.creator.create` function. A maximizing fitness can be created using ::

    create("FitnessMax", (eap.base.Fitness), {"weights" : (1.0,)})


Individual
++++++++++

There is only one rule when building an individual, it **must** contain a :attr:`fitness` attribute. The following all produce valid individuals that are suited for most evolutionary algorithms.

Individual List
---------------

The individual list is suited for binary, integer, float and even funky individuals. It may contain any type and/or any type mix that is needed. The :class:`IndividualList` type is built with ::

    create("IndividualList", (eap.base.List), {"fitness" : eap.base.Fitness})

and an individual is instanciated with ::

    ind = creator.IndividualList(size=5, content=some_random_object_creator)

.. note::
   For individuals containing only a single numeric type, it may be more suited to use the :class:`~eap.base.Array` base class, as the copy operation is way more efficient.

Individual Indices
------------------

The individual indices is almost the same as the individual list, except for the base class. Here we will use the maximizing fitness describes earlier ::

    create("IndividualIndices", (eap.base.Indices), {"fitness" : creator.FitnessMax})

and an individual is instanciated with ::

    ind = creator.IndividualIndices(size=5)

Individual Tree
---------------

Population
++++++++++

A population is usualy a list of individuals or sub-populations, it is no more complicated to create than an individual. ::

    create("Population", (eap.base.List), {"fitness" : eap.base.Fitness})
    
A population of 10 individual indices of *size* 5 is instanciated using ::

    pop = creator.Population(size=10, content=lambda: creator.Individual(size=5))
    
.. note::
   A deme (sub-population) is nomore than another population, it is created the same way as a population (or any other list type).

Encapsulating Types
===================

Type encapsulation one in an other may be a little confusing in this section, it will be made clear in the user's guide :ref:`next section <evo-toolbox>`.