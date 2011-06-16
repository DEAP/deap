.. _short-ga-onemax:

===============================
Short One Max Genetic Algorithm
===============================

The short one max genetic algorithm example is very similar to one max
example. The only difference is that it makes use of the
:mod:`~deap.algorithms` module that implements some basic evolutionary
algorithms. The initialization are the same so we will skip this phase. The
algorithms impemented use specific functions from the toolbox, in this case
:func:`evaluate`, :func:`mate`, :func:`mutate` and :func:`~deap.Toolbox.select`
must be registered. 
::

    toolbox.register("evaluate", evalOneMax)
    toolbox.register("mate", tools.cxTwoPoints)
    toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

The toolbox is then passed to the algorithm and the algorithm uses the
registered function. 
::

    pop = toolbox.population()
    hof = tools.HallOfFame(1)

    algorithms.eaSimple(toolbox, pop, cxpb=0.5, mutpb=0.2, ngen=40, halloffame=hof)

The short GA One max example makes use of a
:class:`~deap.tools.HallOfFame` in order to keep track of the best
individual to appear in the evolution (it keeps them even in the case they
extinguish). All algorithms from the :mod:`~deap.algorithms` module do take a
*halloffame* argument that gets updated after every evaluation section of the
basic algorithms.