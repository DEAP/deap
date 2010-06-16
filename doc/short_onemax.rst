.. _short-ga-onemax:

===============================
Short One Max Genetic Algorithm
===============================

The short one max genetic algorithm example is very similar to one max example. The only difference is that it makes use of the :mod:`~eap.algorithms` module that implements some basic evolutionary algorithms. The initialization are the same so we will skip this phase. The algorithms impemented use specific functions from the toolbox, in this case :func:`evaluate`, :func:`mate`, :func:`mutate` and :func:`~eap.Toolbox.select` must be registered. ::

    tools.register("evaluate", evalOneMax)
    tools.register("mate", toolbox.cxTwoPoints)
    tools.register("mutate", toolbox.mutFlipBit, indpb=0.05)
    tools.register("select", toolbox.selTournament, tournsize=3)

The toolbox is then passed to the algorithm and the algorithm uses the registered function.