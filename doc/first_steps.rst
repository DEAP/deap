.. _first-steps:

========================
First Steps of Evolution
========================

Before starting with complex algorithms, we will see some basis of EAP. First, we will start by creating simple individuals and make them interact with each other. After, we will learn how to use different operators, and then, we will learn how to use the :class:`~eap.toolbox.Toolbox` in order to build the desired structures.

A First Individual
==================

First open a python console and import the :mod:`eap.base` and :mod:`eap.creator` modules. ::

    >>> from eap import base
    >>> from eap import creator

From the :mod:`~eap.creator` module you can now build your first individual class using any base type defined in python or by yourself. Lets create an individual class that inherits from :class:`list` containing a maximizing :attr:`fitness` attribute. ::

    >>> creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    >>> creator.create("Individual", list, fitness=creator.FitnessMax)

The class :class:`list` requires 0 or 1 argument, in order to create an empty or initialized list. We want to create an initialized list so it is convenient to pass a single argument to the individual that is, as defined by the :class:`list` class, a simple iterable object. ::

    >>> content = [1.0 for i in xrange(5)]
    >>> creator.Individual(content)
    [1.0, 1.0, 1.0, 1.0, 1.0]

The content provided to the individual is not very useful since all individuals will be the same. The usual way to provide some randomness is to use functions from the :mod:`random` module as content provider. ::

    >>> import random
    >>> content = lambda: [random.random() for i in xrange(5)]
    >>> creator.Individual(content())
    [0.50, 0.18, 0.76, 0.01, 0.58]
    >>> creator.Individual(content())
    [0.32, 0.41, 0.12, 0.91, 0.67]

Mutation
========

The first kind of operator that we will present is the mutation operator. There is a variety of mutation operators in the :mod:`eap.toolbox` module. Each mutation has its own caracteristics and may be applied to different type of individual. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for mutation operators is that they **only** mutate, this means that an independant copy must be made prior to mutating the individual if the original individual has to be kept or is a reference to an other instance of individual (see the selection operator).

In order to apply a mutation (here a gaussian mutation) on an individual, simply apply the desired function. ::

    >>> from eap import toolbox
    >>> ind = creator.Individual(content())
    >>> toolbox.mutGaussian(ind, sigma=0.2, indpb=0.2)
    >>> del ind.fitness.values

Crossover
=========

The second kind of operator that we will present is the crossover operator. There is a variety of crossover operators in the :mod:`eap.toolbox` module. Each crossover has its own caracteristics and may be applied to different type of individuals. Be carefull to read the documentation of the selected operator in order to avoid undesirable behavior.

The general rule for crossover operators is that they **only** mutate, this means that an independant copy must be made prior to mutating the individual if the original individual has to be kept or is a reference to an other instance of individual (see the selection operator).

Lets create two individuals using the same technique as before, and apply the crossover operation to produce the two children. ::

    >>> ind1 = creator.Individual(content())
    >>> ind2 = creator.Individual(content())
    >>> toolbox.cxBlend(ind1, ind2, 0.5)
    >>> del ind1.fitness.values
    >>> del ind2.fitness.values

Evaluation
==========

The evaluation is the most crucial part of an evolutionary algorithm, it is also the only part of the library that you must write your-self. An typical evaluation function takes one individual as argument and return its fitness as a :class:`tuple`. As shown in the in the :ref:`Evolutionary Algorithm Bases <ea-bases>` section, a fitness is a list of floating point values and has a property :attr:`valid` to know if this individual shall be re-evaluated. The fitness is set by setting the :attr:`~eap.base.Fitness.values` to the associated :class:`tuple`. ::

    >>> def eval(individual):
    ...     # Do some hard computing on the individual
    ...     a = sum(individual)
    ...     b = len(individual)
    ...     return a, 1. / b
    ...         
    >>> child1.fitness.values = eval(child1)
    >>> print child1.fitness
    eap.creator.FitnessMax((1.7, 0.2))
    >>> child2.fitness.values = eval(child2)
    >>> print child2.fitness
    eap.creator.FitnessMax((2.23, 0.2))
    >>> print child1.fitness.valid
    True
    

Selection
=========

Selection is made among a population by the selection operators that are available in the :mod:`eap.toolbox` module. The selection operator usually takes as first argument an iterable container of individuals and the number of individuals to select. It returns a list containing the references to the selected individuals. The selection is made as follow. ::

    >>> selected = toolbox.selBest([child1, child2], n=1)
    >>> selected[0] is child2
    True

.. warning:: It is **very** important here to note that the selection operators does not duplicate any individual during the selection process. If an individual is selected twice and one of either object is modified, the other will also be modified. Only a reference to the individual is copied.

The Toolbox
===========

The toolbox is intended to contain all the evolutionary tools, from the object constructors to the evaluation operator. It allows easy configuration of each algorithms (discussed later). The toolbox has basicaly two methods, :meth:`~eap.toolbox.Toolbox.register` and :meth:`~eap.toolbox.Toolbox.unregister`, that are used to add or remove tools from the toolbox. The toolbox makes it very easy to build a population. Usualy this is done in a python file instead of a console. Lets look at a basic example. ::

    from eap import base
    from eap import creator
    from eap import toolbox
    from random import uniform
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    creator.create("Population", list)
    
    tools = toolbox.Toolbox()
    
    tools.register("attr_flt", uniform, 0, 10)   # Will roll floats between 0 and 10
    
    tools.register("individual", creator.Individual, content_init=tools.attr_flt, size_init=5)
    tools.register("population", creator.Population, content_init=tools.individual, size_init=10)
    
    pop = tools.population()
    
The first three :func:`~eap.creator.create` calls do create the needed classes. Then three construction methods are registered in the toolbox, they add to the toolbox three methods :meth:`attr_flt`, :meth:`individual` and :meth:`population` that can be used as object constructors. It may not seem that simple at first look, but the complexity to add some more stuff is not quite big. In order to add fancy demes of class :class:`Deme` in our population, we only need to add two lines and modify the registration of the population. ::

    creator.create("Deme", list)
    
    tools.register("deme", creator.Deme, content_init=tools.individual, size_init=10)
    tools.register("population", creator.Population, content_init=tools.deme, size_init=3)

Lets make it even harder, lets build two populations of different individuals. The first kind of individual has boolean (``b`` suffix) attributes with a minimizing fitness and the second kind is a mix of integers and floats (``if`` suffix) with a maximizing fitness. ::

    from eap import base
    from eap import creator
    from eap import toolbox
    from random import random, choice, randint
    
    # A funky generator of subsequent int and float
    def if_generator(size, min, max):
        for i in range(size):
            if i % 2 == 0:
                yield randint(min, max)
            else:
                yield random()
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual_b", list, fitness=creator.FitnessMin)
    creator.create("Individual_if", list, fitness=creator.FitnessMax)
    creator.create("Population_b", list)
    creator.create("Population_if", list)
    
    tools = toolbox.Toolbox()
    
    tools.register("attr_b", choice, (True, False))
    tools.register("attr_if", if_generator, 5, 0, 10)
    
    tools.register("individual_b", creator.Individual_b, content_init=tools.attr_b, size_init=5)
    tools.register("individual_if", creator.Individual_if, content_init=tools.attr_if)
    tools.register("population_b", creator.Population_b, content_init=tools.individual_b, size_init=10)
    tools.register("population_if", creator.Population_if, content_init=tools.individual_if, size_init=10)
    
    boolean_pop = tools.population_b()
    integer_float_pop = tools.population_if()

Now the only limit is your imagination.

The Algorithms
==============

There is several algorithms implemented in some modules, but principaly in the :mod:`~eap.algorithms` module. They are very simple and reflects the basic types of evolutionary algorithms present in the litterature. The algorithms use the :class:`~eap.toolbox.Toolbox` as a container for the evolutionary operators so any operator can be used in any algorithm. In order to setup a toolbox for an algorithm, you must register the desired operators under a specified names, usualy the names are :func:`mate` for the crossover operator, :func:`mutate` for the mutation operator, :func:`~eap.Toolbox.select` for the selection operator and last but not least :func:`evaluate` for the evaluation operator. The :class:`~eap.toolbox.Toolbox` uses :func:`functools.partial` functions internaly so you can register the operator's default arguments within the toolbox. The following lines of code register the 4 basic operators and their default arguments in order to setup a toolbox for the :func:`~eap.algorithms.eaSimple` algorithm. ::

    from eap import toolbox
    
    tools = toolbox.Toolbox()
    tools.register("mate", toolbox.cxBlend, alpha=0.5)
    tools.register("mutate", toolbox.mutGaussian, sigma=0.3)
    tools.register("select", toolbox.selTournament, tournsize=3)
    tools.register("evaluate", eval)
    
Now that the toolbox is ready, it is time to launch the algorithm. The simple evolutionary algorithm takes 5 arguments, a *toolbox*, a *population*, a propability of mating each individual at each generation (*cxpb*), a propability of mutating each individual at each generation (*mutpb*) and a max number of generations (*ngen*). ::

    from eap import algorithms
    
    algorithms.eaSimple(tools, pop, cxpb=0.5, mutpb=0.2, ngen=50)

The best way to understand what the simple evolutionary algorithm does, it to take a look at the source code or the documentation.

Now that you built your own evolutionary algorithm in python, you are welcome to gives us feedback and appreciation. We would also really like to hear about your project and success stories with EAP.
