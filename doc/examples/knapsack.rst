==============================
Individual Inheriting from Set
==============================

Again for this example we will use a very simple problem, the 0-1 Knapsack.
The purpose of this example is to show the simplicity of DEAP and the ease to
inherit from anyting else than a simple list or array.

Many evolutionary algorithm textbooks mention that the best way to have an
efficient algorithm to have a representation close the problem. Here, what can
be closer to a bag than a set? Lets make our individuals inherit from the
:class:`set` class. ::

    creator.create("FitnessMulti", base.Fitness, weights=(-1.0, 1.0))
    creator.create("Individual", set, fitness=creator.FitnessMulti)

That's it. You now have individuals that are in fact sets, they have the usual
attribute :attr:`fitness`. The fitness is a
minimization of the first objective (the weight of the bag) and a maximization
of the second objective (the value of the bag). We will now create a
dictionary of 100 random items to map the values and weights. 
::

    # The items' name is an integer, and value is a (weight, value) 2-tuple
    items = dict([(i, (random.randint(1, 10), random.uniform(0, 100))) for i in xrange(100)])

We now need to initialize a population and the individuals therein. For this
we will need a :class:`~deap.base.Toolbox` to register our generators since
sets can also be created with an input iterable. 
::

	toolbox = base.Toolbox()
    
	# Attribute generator
	toolbox.register("attr_item", random.choice, items.keys())
    
	# Structure initializers
	toolbox.register("individual", tools.initRepeat, creator.Individual, n=30)
	toolbox.register("population", tools.initRepeat, list)
    
Voilà! The *last* thing to do is to define our evaluation function.
::

    def evalKnapsack(individual):
        weight = 0.0
        value = 0.0
        for item in individual:
            weight += items[item][0]
            value += items[item][1]
        if len(individual) > MAX_ITEM or weight > MAX_WEIGHT:
            return 10000, 0             # Ensure overweighted bags are dominated
        return weight, value

Everything is ready for evolution. Ho no wait, since DEAP's developers are
lazy, there is no crossover and mutation operators that can be applied
directly on sets. Lets define some. For example, a crossover, producing two child from two parents, could be that the first child is the
intersection of the two sets and the second child their absolute difference.
::

    def cxSet(ind1, ind2):
        """Apply a crossover operation on input sets. The first child is the
        intersection of the two sets, the second child is the difference of the
        two sets.
        """
        temp = set(ind1)                # Used in order to keep type
        ind1 &= ind2                    # Intersection (inplace)
        ind2 ^= temp                    # Symmetric Difference (inplace)

A mutation operator could randomly add or remove an element from the set
input individual. 
::

    def mutSet(individual):
        """Mutation that pops or add an element."""
        if random.random() < 0.5:
            if len(individual) > 0:     # Can't pop from an empty set
                mutant.pop()
        else:
            mutant.add(random.choice(items.keys()))

.. note::
   The outcome of this mutation is dependent of the python you use. The
   :meth:`set.pop` function is not consistent between versions of python. See
   the sources of the actual example for a version that will be stable but
   more complicated.

From here, everything else is just as usual, register the operators in the
toolbox, and use or write an algorithm. Here we will use the :func:`~deap.algorithms.eaMuPlusLambda`
algorithm and the SPEA-II selection scheme. 
::

	toolbox.register("evaluate", evalKnapsack)
	toolbox.register("mate", cxSet)
	toolbox.register("mutate", mutSet)
	toolbox.register("select", tools.selSPEA2)
	
	pop = toolbox.population(n=MU)
	hof = tools.ParetoFront()
	stats = tools.Statistics(lambda ind: ind.fitness.values)
	stats.register("Avg", tools.mean)
	stats.register("Std", tools.std)
	stats.register("Min", min)
	stats.register("Max", max)
	
	algorithms.eaMuPlusLambda(toolbox, pop, MU, LAMBDA, CXPB, MUTPB, MAXGEN, stats, hof)

Finally, a :class:`~deap.tools.ParetoFront` may be used to retrieve the best
non dominated individuals of the evolution and a
:class:`~deap.tools.Statistics` object is created for compiling four different
statistics over the generations. The complete `Knapsack Genetic Algorithm
<http://deap.googlecode.com/hg/examples/ga_knapsack.py>`_ code is available.
