.. _spambase:
    
=======================
STGP example : Spambase
=======================

This problem is a classification example using STGP (Strongly Typed Genetic Programming). The evolved programs work on floating-point values AND Booleans values. The programs must return a Boolean value which must be true if e-mail is spam, and false otherwise. It uses a base of emails (saved in *spambase.csv*, see :ref:`refPapersSpam`), from which it randomly choose 400 emails to evaluate each individual.

.. warning::
    Don't expect too much from this program as it is quite basic and not oriented toward performance. It is given to illustrate the use of strongly-typed GP with DEAP. From a machine learning perspective, it is mainly wrong.

Primitives set used
===================

Strongly-typed GP is a more generic GP where each primitive, in addition to have an arity and a corresponding function, has also a specific return type and specific parameter(s) type. In this way, each primitive is someway describe as a pure C function, where each parameter has to be one of the good type, and where the return value type is specified before runtime.

.. note::
    Actually, when the user does not specify return or parameters type, a default type is selected by DEAP. On standard GP, because all the primitives use this default type, this behaves as there was no type requirement.
    
We define a typed primitive set almost the same way than a normal one, but we have to also specify the types used. ::
    
    pset = gp.PrimitiveSetTyped("MAIN", itertools.repeat("float", 57), "bool", "IN")

    # boolean operators
    pset.addPrimitive(operator.and_, ["bool", "bool"], "bool")
    pset.addPrimitive(operator.or_, ["bool", "bool"], "bool")
    pset.addPrimitive(operator.not_, ["bool"], "bool")

    # floating point operators
    def safeDiv(left, right):
        try: return left / right
        except ZeroDivisionError: return 0
    pset.addPrimitive(operator.add, ["float","float"], "float")
    pset.addPrimitive(operator.sub, ["float","float"], "float")
    pset.addPrimitive(operator.mul, ["float","float"], "float")
    pset.addPrimitive(safeDiv, ["float","float"], "float")

    # logic operators
    def if_then_else(input, output1, output2):
        if input: return output1
        else: return output2

    pset.addPrimitive(operator.lt, ["float", "float"], "bool")
    pset.addPrimitive(operator.eq, ["float", "float"], "bool")
    pset.addPrimitive(if_then_else, ["bool", "float", "float"], "float")

    # terminals
    pset.addEphemeralConstant(lambda: random.random() * 100, "float")
    pset.addTerminal(0, "bool")
    pset.addTerminal(1, "bool")

On the first line, we see the declaration of a typed primitive set. The first argument remains the set name, but the next ones are the type of the entries (in this case, we have 57 float entries and one boolean output; we could have written `float` 57 times, but it is fairly quickier and more understandable to use the `itertools.repeat <http://docs.python.org/library/itertools.html#itertools.repeat>`_ function). The last argument remains the entries prefix.

After that, we define the primitives themselves. The definition of a typed primitive has two additional parameters : a list containing the parameters type, in order, and the return type.

.. note::
    The types specified do not have to be real Python or C types. In the above example, we may rename "float" in "type1" and "bool" in "type2" without any issue. For the same reason, DEAP nor Python actually check if a given parameter has the good type.

The terminals set is then filled, with at least one terminal of each type, and that is for the primitive set declaration.

Evaluation function
===================

The evaluation function is very simple : it picks 400 mails at random in the spam database, and then checks if the prediction made by the individual matches the boolean output expected. The count of well predicted emails is returned as the fitness of the individual (which is, at most, 400). ::
    
    def evalSpambase(individual):
        # Transform the tree expression in a callable function
        func = tools.lambdify(expr=individual)
        # Randomly sample 400 mails in the spam database (defined before)
        spam_samp = random.sample(spam, 400)
        # Evaluate the sum of correctly identified mail as spam
        result = sum(bool(func(*mail[:57])) is bool(mail[57]) for mail in spam_samp)
        return result,

Toolbox
=======

The toolbox used is very similar to the one presented in the symbolic regression example, but one should notice that we now use specific STGP operators for crossovers and mutations : ::
    
    tools.register("evaluate", evalSpambase)
    tools.register("select", operators.selTournament, tournsize=3)
    tools.register("mate", operators.cxTypedTreeOnePoint)
    tools.register("expr_mut", gp.generateFull, min_=0, max_=2)
    tools.register("mutate", operators.mutTypedTreeUniform, expr=tools.expr_mut)
    

Complete Example
================

This is the complete code for the spambase example. Although it does not really differ from the other problems, it is interesting to note how Python can speed up the programming time. Indeed, the spam database is in csv form : with many frameworks, you would have to manually read it, or use a non-standard library, but with Python, you can use the built-in mode `csv <http://docs.python.org/library/csv.html>`_ and, within 2 lines, it is done! The data is now in a the matrix *spam* and can easily be used through all the program : ::
    
    import csv
    from deap import algorithms
    from deap import base
    from deap import creator
    from deap import gp
    from deap import operators
    from deap import toolbox


    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    # Read the spam list features and put it in a list of lists.
    # The dataset is from http://archive.ics.uci.edu/ml/datasets/Spambase
    # This example is a copy of the OpenBEAGLE example :
    # http://beagle.gel.ulaval.ca/refmanual/beagle/html/d2/dbe/group__Spambase.html
    spamReader = csv.reader(open("spambase.csv"))
    spam = list(list(float(elem) for elem in row) for row in spamReader)

    # defined a new primitive set for strongly typed GP
    pset = gp.PrimitiveSetTyped("MAIN", itertools.repeat("float", 57), "bool", "IN")

    # boolean operators
    pset.addPrimitive(operator.and_, ["bool", "bool"], "bool")
    pset.addPrimitive(operator.or_, ["bool", "bool"], "bool")
    pset.addPrimitive(operator.not_, ["bool"], "bool")

    # floating point operators
    # Define a safe division function
    def safeDiv(left, right):
        try: return left / right
        except ZeroDivisionError: return 0

    pset.addPrimitive(operator.add, ["float","float"], "float")
    pset.addPrimitive(operator.sub, ["float","float"], "float")
    pset.addPrimitive(operator.mul, ["float","float"], "float")
    pset.addPrimitive(safeDiv, ["float","float"], "float")

    # logic operators
    # Define a new if-then-else function
    def if_then_else(input, output1, output2):
        if input: return output1
        else: return output2

    pset.addPrimitive(operator.lt, ["float", "float"], "bool")
    pset.addPrimitive(operator.eq, ["float", "float"], "bool")
    pset.addPrimitive(if_then_else, ["bool", "float", "float"], "float")

    # terminals
    pset.addEphemeralConstant(lambda: random.random() * 100, "float")
    pset.addTerminal(0, "bool")
    pset.addTerminal(1, "bool")

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)

    tools = toolbox.Toolbox()
    tools.register("expr", gp.generateRamped, pset=pset, type_=pset.ret, min_=1, max_=2)
    tools.register("individual", toolbox.fillIter, creator.Individual, tools.expr)
    tools.register("population", toolbox.fillRepeat, list, tools.individual, 100)
    tools.register("lambdify", gp.lambdify, pset=pset)

    def evalSpambase(individual):
        # Transform the tree expression in a callable function
        func = tools.lambdify(expr=individual)
        # Randomly sample 400 mails in the spam database
        spam_samp = random.sample(spam, 400)
        # Evaluate the sum of correctly identified mail as spam
        result = sum(bool(func(*mail[:57])) is bool(mail[57]) for mail in spam_samp)
        return result,
        
    tools.register("evaluate", evalSpambase)
    tools.register("select", operators.selTournament, tournsize=3)
    tools.register("mate", operators.cxTypedTreeOnePoint)
    tools.register("expr_mut", gp.generateFull, min_=0, max_=2)
    tools.register("mutate", operators.mutTypedTreeUniform, expr=tools.expr_mut)

    stats_t = operators.Stats(lambda ind: ind.fitness.values)
    stats_t.register("Avg", operators.mean)
    stats_t.register("Std", operators.std_dev)
    stats_t.register("Min", min)
    stats_t.register("Max", max)

    def main():
        pop = tools.population()
        hof = operators.HallOfFame(1)
        stats = tools.clone(stats_t)
        
        algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, stats, halloffame=hof)
        
        logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)

        return pop, stats, hof

    if __name__ == "__main__":
        main()

.. _refPapersSpam:
    
Reference
=========

Data are from the Machine learning repository, http://www.ics.uci.edu/~mlearn/MLRepository.html