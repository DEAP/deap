============================
Evolutionary Algorithm Bases
============================

.. automodule:: eap.base

Population
==========

.. autoclass:: Population
   :members:

.. autoclass:: PopulationMatrix([rows, columns, generator])
   :members:
   
Individual
==========

.. autoclass:: Individual([size, fitness, generator])
   :members:
   
Fitness
=======

.. autoclass:: Fitness(weights)
   :members:

Attribute
=========

.. versionchanged:: 0.2.1a
   From now, a Gene will be called an attribute, in order to avoid any confusion with biology terminologie that can miss lead the real extent of the individual's attributes.

Version 0.2.1a of EAP elliminated the :class:`Gene` class since any object may be inserted in an :class:`Individual` as an attribute. Instead generator function are used to produce those attributes. In fact, on the initialisation of an individual, the generator's :func:`next` function is simply called repeatedly until the individual has all its attributes.

.. autofunction:: realGenerator(min, max)

.. autofunction:: integerGenerator(min, max)

.. autofunction:: indiceGenerator

.. autofunction:: booleanGenerator