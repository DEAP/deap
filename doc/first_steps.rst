========================
First Steps of Evolution
========================

Before starting with complex algorithms, we will see some basis of EAP. First, we will start by creating simple individuals and make them interact with each other. After, we will learn how to use different operators, and then, we will learn how to use the :class:`~eap.toolbox.Toolbox` in order to build the desired structures.

A First Individual
==================

First open a python console and import the :mod:`eap.base` and :mod:`eap.creator` modules. ::

    >>> import eap.base as base
    >>> import eap.creator as creator

From the :mod:`~eap.creator` module you can now build your first individual class using any base type defined :mod:`~eap.base`. Lets create an :class:`~eap.base.List` individual class containing a maximizing fitness attribute. ::

    >>> creator.create("FitnessMax", (base.Fitness,), {"weights" : (1.0,)})
    >>> creator.create("Individual", (base.List,), {"fitness" : creator.FitnessMax})

The :class:`~eap.base.List` requires 2 arguments, *size* and *content*. First, the *size* argument is the number of attributes that you want in your individual. Second, the *content* argument is a way to provide the content of the individual as described in the :class:`~eap.base.List` documentation. All that said lets build the individual filled with ones. ::

    >>> ind = creator.Individual(size=5, content=lambda: 1.0)
    >>> print ind
    [1.0, 1.0, 1.0, 1.0, 1.0]

The content provided to the individual is not very useful since all individuals will be the same. The usual way to provide some randomness is to use the :func:`random.random` function as content provider. ::

    >>> ind = creator.Individual(size=5, content=lambda: random.random())
    >>> print ind
    [0.50, 0.18, 0.76, 0.01, 0.58]

Mutation
========

The first kind of operator that we will present is the mutation operator. There is a variety of mutation operators in the :mod:`eap.toolbox` module. Each mutation has its own caracteristics and may be applied to different type of individual. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for mutation operators is that they make a copy of the individual before touching it and then apply the mutation on the copied individual. The mutated individual is finaly returned after its fitness has been invalidated.

In order to apply a mutation (here a gaussian mutation) on an individual, simply apply the desired function. ::

    >>> import eap.toolbox as toolbox
    >>> mutant = toolbox.mutGaussian(ind, sigma=0.2, indpb=0.2)
    >>> print mutant
    [0.34, 0.18, 0.76, 0.01, 0.50]
    >>> print type(mutant)
    <class 'eap.creator.Individual'>


Crossover
=========

The second kind of operator that we will present is the crossover operator. There is a variety of crossover operators in the :mod:`eap.toolbox` module. Each crossover has its own caracteristics and may be applied to different type of individuals. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for crossover operators is that they return children that are independent of their parents and do not touch to the parents configuration. The returned children have invalid fitness.

Lets create a second individual using the same technique as before, and apply the crossover operation. ::

    >>> ind2 = creator.Individual(size=5, content=lambda: random.random())
    >>> child1, child2 = toolbox.cxBlend(ind, ind2, 0.5)
    >>> print child1
    [0.11, 0.25, 0.67, 0.09, 0.58]
    >>> print child2
    [0.53, 0.24, 0.75, 0.13, 0.58]


Now we have two different individuals and their respective child. Both of the children have an invalid fitness.

Evaluation
==========

The evaluation is the most crucial part of an evolutionary algorithm, it is also the only part of the library that you must write your-self. An typical evaluation function takes one invidual as argument and set or return its fitness. As shown in the in the :ref:`Evolutionary Algorithm Bases <ea-bases>` section, a fitness is an array of floating point values and has a property :attr:`valid` to know if this individual shall be re-evaluated. An invalid fitness is necessary empty, so the method for setting each fitness value is by appending subsequently each fitness value to the fitness (or simply extending the fitness). Here is an example of a basic fitness calculation. ::

    >>> def eval(individual):
    ...     # Do some calculation on the individual
    ...     a = sum(individual)
    ...     b = len(individual)
    ...     return a, 1. / b
    ...         
    >>> child.fitness.extend(eval(child1))
    >>> print child1.fitness
    array('d', [1.7, 0.2])
    >>> child2.fitness.extend(eval(child2))
    >>> print child2
    array('d', [2.23, 0.2])
    >>> print child.fitness.valid
    True
    

Selection
=========

Selection is made among a population by the selection operators that are availables in the :mod:`eap.toolbox` module. The selection operator usualy takes as first argument an iterable container of individuals and the number of individuals to select. It returns a list containing the tag of the selected individuals. The selection is made as follow. ::

    >>> selected = toolbox.selBest([child1, child2], n=1)
    >>> print selected[0]
    [0.53, 0.24, 0.75, 0.13, 0.58]
    >>> selected[0] is child2
    True

.. warning:: It is **very** important here to note that the selection operators does not duplicate any individual during the selection process. If an individual is selected twice and one of either object is modified, the other will also be modified. Only a reference to the individual is copied.

The Toolbox
===========

The toolbox is intended to contain all the evolutionary tools, from the object constructors to the evaluation operator. It allows easy configuration of each algorithms (discussed later). The toolbox has basicaly two methods, :meth:`register` and :meth:`unregister`, that are used to add or remove tools from the toolbox. The toolbox makes it very easy to build a population. Usualy this is done in a python file instead of a console. Lets look at a basic example. ::

    import eap.base as base
    import eap.creator as creator
    import eap.toolbox as toolbox
    from random import random
    
    creator.create("FitnessMax", (base.Fitness,), {"weights" : (1.0,)})
    creator.create("Individual", (base.List,), {"fitness" : creator.FitnessMax})
    creator.create("Population", (base.List,))
    
    tools = toolbox.Toolbox()
    tools.register("individual", creator.Individual, size=5, content=lambda: random())
    tools.register("population", creator.Population, size=10, content=tools.individual)
    
    pop = tools.population()
    
The first three :func:`~eap.creator.create` calls do create the needed classes. Then two construction methods are registered in the toolbox, they add to the toolbox two methods :meth:`individual` and :meth:`population` that can be used as object constructors as in the last line, :meth:`population` do build a population as declared in the toolbox. It may not seem that simple at first look, but the complexity to add some more stuff is not quite big. In order to add fancy demes of class :class:`Deme` in our population, we only need to add two lines and modify the registration of the population. ::

    creator.create("Deme", (base.List,))
    
    tools.register("deme", creator.Population, size=10, content=tools.individual)
    tools.register("population", creator.Population, size=3, content=tools.deme)

Lets make it even harder, lets build two populations of different individuals. The first kind of individual has boolean (``b`` sufix) attributes with a minimizing fitness and the second kind is a mix of integers and floats (``if`` sufix) with a maximizing fitness. ::

    import eap.base as base
    import eap.creator as creator
    import eap.toolbox as toolbox
    import random
    
    # A funky generator of subsequent int and float
    def if_generator(size, min, max):
        for i in range(size):
            if i % 2 == 0:
                yield random.randint(min, max)
            else:
                yield random.random((True, False))
    
    creator.create("FitnessMax", (base.Fitness,), {"weights" : (1.0,)})
    creator.create("Individual_b", (base.List,), {"fitness" : base.Fitness})
    creator.create("Individual_if", (base.List,), {"fitness" : creator.FitnessMax})
    creator.create("Population_b", (base.List,))
    creator.create("Population_if", (base.List,))
    
    tools = toolbox.Toolbox()
    tools.register("individual_b", creator.Individual_b, size=5, content=lambda: random.choice((True. False)))
    tools.register("individual_if", creator.Individual_if, content=if_generator(5, 0, 10))
    tools.register("population_b", creator.Population_b, size=10, content=tools.individual_b)
    tools.register("population_if", creator.Population_if, size=10, content=tools.individual_if)
    
    boolean_pop = tools.b_population()
    integer_float_pop = tools.if_population()

Now the only limit is your imagination.

The Algorithms
==============

There is several algorithms implemented in some modules, but principaly in the :mod:`~eap.algorithms` module. They are very simple and reflects the basic types of evolutionary algorithms present in the litterature. The algorithms use the :class:`~eap.toolbox.Toolbox` as a container for the evolutionary operators so any operator can be used in any algorithm. In order to setup a toolbox for an algorithm, you must register the desired operators under a specified names, usualy the names are ``mate`` for the crossover operator, ``mutate`` for the mutation operator, ``select`` for the selection operator and last but not least ``evaluate`` for the evaluation operator. The :class:`~eap.toolbox.Toolbox` uses :func:`functools.partial` functions internaly so you can register the operator's default arguments within the toolbox. The following lines of code register the 4 basic operators and their default arguments in order to setup a toolbox for the :func:`~eap.algorithms.simpleEA` algorithm. ::

    import eap.toolbox as toolbox
    
    tools = toolbox.Toolbox()
    tools.register("mate", toolbox.cxBlend, alpha=0.5)
    tools.register("mutate", toolbox.mutGaussian, sigma=0.3)
    tools.register("select", toolbox.selTournament, tournsize=3)
    tools.register("evaluate", eval)
    
Now that the toolbox is ready, it is time to launch the algorithm. The simple evolutionary algorithm takes 5 arguments, a *toolbox*, a *population*, a propability of mating each individual at each generation (*cxpb*), a propability of mutating each individual at each generation (*mutpb*) and a max number of generations (*ngen*). ::

    import eap.algorithms as algorithms
    
    algorithms.eaComma(tools, pop, 0.5, 0.2, 50)
    algorithms.simpleEA(tools, pop, 0.5, 0.2, 50)

The best way to understand what the simple evolutionary algorithm does, it to take a look at the source code or the documentation. Now that you built your own evolutionary algorithm in python, you are welcome to gives us feedback and appreciation. We would also really like to hear about your project and success stories with EAP.
