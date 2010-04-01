========================
First Steps of Evolution
========================

.. warning::
   This documentation is out of date as of version 0.4. See the :ref:`ga-onemax` tutorial and :ref:`ea-bases` for details on version 0.4.x.

Before starting with complex algorithms, we will see some basis of EAP. First, we will start by creating simple individuals and make them interact with each other. After, we will learn how to use different operators. And then, we will learn how to use the :class:`~eap.toolbox.Toolbox` in order to build the desired structures

A First Individual
==================

First open a python console and import the :mod:`eap.base` module. ::

    >>> import eap.base as base

From the :mod:`~eap.base` module you can now build your first individual of any kind defined in the :mod:`~eap.base` module. Lets build an :class:`~eap.base.Individual` composed of boolean attributes and a maximizing fitness. The :class:`~eap.base.Individual` requires 3 arguments, *size*, *generator* and *fitness*. First, the *size* argument is the number of attributes that you want in your individual. Second, the *generator* argument is a generator function (providing a :func:`next` function) that will generate each attribute of the individual. Finaly, the *fitness* argument is the constructor object of the fitness that you want to associate with your individual. All that said lets build the individual. ::

    >>> base.Individual(size=5, generator=base.booleanGenerator(),
    ...				fitness=base.Fitness(weights=(1.0,))
    [False, False, True, False, True]: []

The individual created is probably different from the one created here. This is due to the use of the python's :mod:`random` module in the :func:`~eap.base.booleanGenerator` function. In order to control the randomness, we usualy set the seed of the :mod:`random` so the results are repeatable. ::

    >>> import random
    >>> random.seed(1024)
    >>> base.Individual(size=5, generator=base.booleanGenerator(),
    ...				fitness=base.Fitness(weights=(1.0,))
    [True, False, False, True, True]: []

Now you should have the same individual as in the example (remember that the random module is os dependent).

Mutation
========

The first kind of operator that we will present is the mutation operator. There is a variety of mutation operators in the :mod:`eap.toolbox` module. Each mutation has its own caracteristics and may be applied to different type of individual. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for mutation operators is that they make a copy of the individual before touching it and then apply the mutation on the copied individual. The mutated individual is finaly returned after its fitness has been invalidated.

In order to apply a mutation (here a bit inversion mutation) on an individual, simply apply the desired function. ::

    >>> import eap.operators as operators
    >>> operators.flipBitMut(ind1, flipIndxPb=0.2)
    [False, False, False, True, True]: []

Crossover
=========

The second kind of operator that we will present is the crossover operator. There is a variety of crossover operators in the :mod:`eap.toolbox` module. Each crossover has its own caracteristics and may be applied to different type of individuals. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for crossover operators is that they return childrens that are independent of their parents and do not touch to the parents configuration. The returned childrens have invalid fitness.

Lets create a second individual using the same technique as before, and apply the crossover operation. ::

    >>> ind2 = base.Individual(size=5, generator=base.booleanGenerator(),
    ... 		   fitness=base.Fitness(weights=(1.0,))
    >>> toolbox.twoPointsCx(ind1, ind2)
    ([True, True, False, True, True]: [], [False, False, True, True, True]: [])

Now we have two different individuals and their respective child. Both of the childrens have an invalid fitness.

Evaluation
==========

The evaluation is the most crucial part of an evolutionary algorithm, it is also the only part of the library that you must write your-self. An typical evaluation function takes one invidual as argument and set or return its fitness. As shown in the in the :ref:`Evolutionary Algorithm Bases <ea-bases>` section, a fitness is an array of floating point values and has a method :meth:`isValid` to know if this individual shall be re-evaluated. An invalid fitness is necessary empty, so the method for setting each fitness value is by appending subsequently each fitness value to the fitness (or simply extending the fitness). Here is an example of a basic fitness calculation. ::

    >>> def eval(individual):
    ...     # Try to save some work
    ...     if not individual.mFitness.isValid():
    ...         # Do some calculation on the individual
    ...         a = sum(individual)
    ...         b = len(individual)
    ...         individual.mFitness.append(a)
    ...         individual.mFitness.append(1.0/b)
    ...         
    >>> eval(child1)
    >>> print child1
    [True, True, False, True, True]: [4.0, 0.2]
    >>> eval(child2)
    >>> print child2
    [False, False, True, True, True]: [3.0, 0.2]
    

Selection
=========

Selection is made among a population by the selection operators that are availables in the :mod:`eap.toolbox` module. The selection operator usualy takes as first argument an iterable container of individuals and the number of individuals to select. It returns a list containing the tag of the selected individuals. The selection id made as follow. ::

    >>> toolbox.bestSel([child1, child2], n=1)
    [[True, True, False, True, True]: [4.0, 0.2]]

.. warning:: It is **very** important here to note that the selection operators does not duplicate any individual during the selection process. If an individual is selected twice and one of either object is modified, the other will also be modified. Only the reference on the individual is copied.

The Toolbox
===========

The toolbox is intended to contain all the evolutionary tools, from the object constructors to evaluation operator. It allows easy configuration of each algorithms (discussed later). The toolbox has basicaly two methods, :meth:`register` and :meth:`unregister`, that are used to add or remove tools from the toolbox. The toolbox makes it very easy to build a population. Lets look at a basic example. ::

    import eap.base as base
    import eap.toolbox as toolbox
    
    lToolbox = toolbox.Toolbox()
    lToolbox.register('fitness', base.Fitness, weights=(1.0,))
    lToolbox.register('individual', base.Individual, size=5, generator=base.booleanGenerator(),
                fitness=lToolbox.fitness)
    lToolbox.register('population', base.Population, size=10, generator=lToolbox.individual)
    
    lPopulation = lToolbox.population()
    
The first three :meth:`register` calls do add tools to build evolutionary objects, in fact they add to the toolbox three methods :meth:`fitness`, :meth:`individual` and :meth:`population` that can be used as object constructors as in the last line, :meth:`population` do build a population as declared in the toolbox. It may not seem that simple at first look but, the complexity to add some more stuff is not quite big. In order to add demes in our population, we only need to replace the population registration line by changing its generator ::

    import eap.base as base
    import eap.toolbox as toolbox
    
    lToolbox = toolbox.Toolbox()
    lToolbox.register('fitness', base.Fitness, weights=(1.0,))
    lToolbox.register('individual', base.Individual, size=5, generator=base.booleanGenerator(),
                fitness=lToolbox.fitness)
    lToolbox.register('deme', base.Population, size=10, generator=lToolbox.individual)
    lToolbox.register('population', base.Population, size=5, generator=lToolbox.deme)
    
    lPopulation = lToolbox.population()

Lets make it even harder, lets build two populations of different individuals. The first kind of individual has boolean attributes and the second kind is a mix of integers and floats. ::

    import eap.base as base
    import eap.toolbox as toolbox
    
    lToolbox = toolbox.Toolbox()
    lToolbox.register('fitness', base.Fitness, weights=(1.0,))
    lToolbox.register('bIndividual', base.Individual, size=5, fitness=lToolbox.fitness,
            generator=base.booleanGenerator())
    lToolbox.register('ifIndividual', base.Individual, size=5, fitness=lToolbox.fitness, 
            generator=[base.integerGenerator(0, 10), base.floatGenerator(0, 1)])
    lToolbox.register('bPopulation', base.Population, size=10, generator=lToolbox.bIndividual)
    lToolbox.register('ifPopulation', base.Population, size=10, generator=lToolbox.ifIndividual)
    
    lBooleanPop = lToolbox.bPopulation()
    lIntegerFloatPop = lToolbox.ifPopulation()

Now the only limit is your imagination.

The Algorithms
==============
