.. _ea-bases:

============================
Evolutionary Algorithm Bases
============================

.. automodule:: eap.base

.. _containers:

Container Types
===============

.. autoclass:: eap.base.List([size, content])

.. autoclass:: eap.base.Array(typecode[, size, content])

.. autoclass:: eap.base.Indices(size)

.. autoclass:: eap.base.Tree([content])

The Creator
===========

Population
==========
   
Individual
==========
   
Fitness
=======

.. autoclass:: Fitness
   :members:

Attribute
=========

.. versionchanged:: 0.4.0
   While in version 0.2.1a :class:`Genes` were removed in favor of attributes generator, version 0.4.0 does not use implicite attribute generator. Intead, :ref:`containers` may be initialized by more than one method including the use of generator functions, iterables and callables.
   
Here is an example of how to implement a generator function that produce a serie of boolean and integer that may be used to produce individuals. ::

    def myGenerator(size, min, max):
        i = 0
        while i < size:
            if i % 2 == 0:
                yield random.choice((True, False))
            else:
                yield random.randint(min, max)
            i += 1
        raise StopIteration
