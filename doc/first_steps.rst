========================
First steps of evolution
========================

Before starting with complex algorithms, we will see some basis of EAP. First, we will start by creating simple individuals and make them interact with each other. After, we will learn how to use different operators. And then, we will learn how to use the :class:`~eap.creator.Creator` in order to build the desired structures

A first individual
==================

.. automodule: eap.base

.. automodule: eap.operators

First open a python console and import the :mod:`eap.base` module. ::

    >>> import eap.base as base

From the :mod:`~eap.base` module you can now build your first individual of any kind defined in the :mod:`~eap.base` module. Lets build a :class:`~eap.base.ListIndividual` composed of boolean attributes and a maximizing fitness. The :class:`~eap.base.ListIndividual` requires 3 arguments, *size*, *generator* and *fitness*. First, the *size* argument is the number of attributes that you want in your individual. Second, the *generator* argument is a generator function (providing a :func:`next` function) that will generate each attribute of the individual. Finaly, the *fitness* argument is the constructor object of the fitness that you want to associate with your individual. All that said lets build the individual. ::

    >>> ind = base.ListIndividual(size=5, generator=base.booleanGenerator(),
    				fitness=base.Fitness(weights=(1.0,))
    >>> print ind
    [False, False, True, False, True]: []

The individual created is probably different from the one created here. This is due to the use of the python's :mod:`random` module in the :func:`~eap.base.booleanGenerator` function. In order to control the randomness, we usualy set the seed of the :mod:`random` so the results are repeatable. ::

    >>> import random
    >>> random.seed(1024)
    >>> ind1 = base.ListIndividual(size=5, generator=base.booleanGenerator(),
    				fitness=base.Fitness(weights=(1.0,))
    >>> print ind1
    [True, False, False, True, True]: []

Now you should have the same individual as in the example (remember that the random module is os dependent).

Mutation
========

The first kind of operator that we will present is the mutation operator. There is a variety of mutation operators in the :mod:`eap.operators` module. Each mutation has its own caracteristics and may be applied to different type of individual. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for mutation operators is that they make a copy of the individual before touching it and then apply the mutation on the copied individual. The mutated individual is finaly returned after its :class:`Fitness` has been invalidated.

In order to apply a mutation (here a bit inversion mutation) on an individual, simply apply the desired function. ::

    >>> import eap.operators as operators
    >>> m_ind1 = operators.flipBitMut(ind1, flipIndxPb=0.2)
    >>> print m_ind1
    [False, False, False, True, True]: []



Crossover
=========

The second kind of operator that we will present is the crossover operator. There is a variety of crossover operators in the :mod:`eap.operators` module. Each crossover has its own caracteristics and may be applied to different type of individuals. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for crossover operators is that they return childrens that are independent of their parents and do not touch to the parents configuration. The returned childrens have invalid fitness.

Lets create a second individual using the same technique as before, and apply the crossover operation. ::

    >>> ind2 = base.ListIndividual(size=5, generator=base.booleanGenerator(),
    				fitness=base.Fitness(weights=(1.0,))
    >>> child1, child2 = operators.twoPointsCx(ind1, ind1)
    >>> print child1
    [True, True, False, True, True]: []
    >>> print child2
    [False, False, True, True, True]: []

Now we have two different individuals and their respective children.

Selection
=========

Selection is made among a population by the selection operators that are availables in the :mod:`eap.operators` module. 

Evaluation
==========

The evolutionary tools
======================

The toolbox
-----------------

The creator
-----------------
