==============================
Individual Inheriting from Set
==============================

Again for this example we will use a very simple problem, the 0-1 Knapsack. The purpose of this example is to show the simplicity of EAP and the ease to inherit from anyting else than a simple list or array.

Many evolutionary algorithm textbooks mention that the best way to have an efficient algorithm to have a representation close the problem. Here, what can be closer to a bag than a set? Lets make our individuals inherit from the :class:`set` class. ::

    creator.create("Fitness", base.Fitness, weights=(-1.0, 1.0))
    creator.create("Individual", set, fitness=creator.Fitness)
    creator.create("Population", list)

That's it. You now have individuals that are in fact sets, they have the usual attribute :attr:`fitness` that shall contain an individual. The fitness is a minimization of the first objective (the weight of the bag) and a maximization of the second objective (the value of the bag). Finally, the last line is simply to pretty print the :class:`Population`\ 's type whith function :func:`type`. We will now create a dictionary of 100 items to map the values and weights. ::

    # The items' name is an integer, and value is a (weight, value) 2-uple
    items = dict([(i, (random.randint(1, 10), random.uniform(0, 100))) for i in xrange(100)])

We now need to initialize a population and the individuals there in. For this we will need a :class:`~eap.toolbox.Toolbox` to register our generators since sets can also be created with an input iterable. ::

    tools = toolbox.Toolbox()
    
    # Attribute generator
    tools.register("attr_item", random.choice, items.keys())
    
    # Structure initializers
    tools.register("individual", creator.Individual, content_init=tools.attr_item, size_init=30)
    tools.register("population", creator.Population, content_init=tools.individual, size_init=100)

A population is now initialized with ::

    pop = tools.population()
    
Voilà! The *last* thing to do is to define our evaluation function ::

    def evalKnapsack(individual):
        weight = 0.0
        value = 0.0
        for item in individual:
            weight += items[item][0]
            value += items[item][1]
        if len(individual) > MAX_ITEM or weight > MAX_WEIGHT:
            return 10000, 0             # Ensure overweighted bags are dominated
        return weight, value

Everything is ready for evolution. Ho no wait, since EAP's developpers are lazy, there is no crossover and mutation operators that can be applyed directly on sets available. Lets build some then. A crossover may be, for example, producing two child from two parents, the first child would be the intersection of the two sets and the second child their absolute difference. ::

    def cxSet(ind1, ind2):
        """Apply a crossover operation on input sets. The first child is the
        intersection of the two sets, the second child is the difference of the
        two sets.
        """
        temp = set(ind1)                # Used in order to keep type
        ind1 &= ind2                    # Intersection (inplace)
        ind2 ^= temp                    # Symmetric Difference (inplace)

And a mutation operator could randomly add or remove an element from the set input individual. ::

    def mutSet(individual):
        """Mutation that pops or add an element."""
        if random.random() < 0.5:
            if len(individual) > 0:     # Cannont pop from an empty set
                mutant.pop()
        else:
            mutant.add(random.choice(items.keys()))

From here, everything else is just as usual, register the operators in the toolbox, and use or write an algorithm. Here we will use the Mu+Lambda algorithm and the SPEA-II selection sheme. ::

    tools.register("evaluate", evalKnapsack)
    tools.register("mate", cxSet)
    tools.register("mutate", mutSet)
    tools.register("select", toolbox.spea2)
    
    pop = tools.population()
    hof = ParetoFront()
    
    algorithms.eaMuPlusLambda(tools, pop, 50, 100, 0.7, 0.2, 50, hof)

Finally, a :class:`~eap.halloffame.ParetoFront` may be used to retreive the best individuals of the evolution. The complete `Knapsack Genetic Algorithm <http://deap.googlecode.com/hg/examples/ga_onemax.py>`_ code is available.
