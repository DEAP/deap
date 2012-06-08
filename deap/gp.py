#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

"""The :mod:`gp` module provides the methods and classes to perform
Genetic Programming with DEAP. It essentially contains the classes to
build a Genetic Program Tree, and the functions to evaluate it.

This module support both strongly and loosely typed GP.
"""


import copy
import random
import sys

from collections import defaultdict

import base

# Define the name of type for any types.
__type__ = None

## GP Tree utility functions

def evaluate(expr, pset=None):
    """Evaluate the expression *expr* into a string if *pset* is None
    or into Python code if *pset* is not None.
    """
    def _stringify(expr):
        try:
            func = expr[0]
            return str(func(*[_stringify(value) for value in expr[1:]]))
        except TypeError:
            return str(expr)
    if not pset is None:
        try:
            return eval(_stringify(expr), pset.functions)
        except MemoryError:
            _, _, traceback = sys.exc_info()
            raise MemoryError, ("DEAP : Error in tree evaluation :"
            " Python cannot evaluate a tree with a height bigger than 90. "
            "To avoid this problem, you should use bloat control on your "
            "operators. See the DEAP documentation for more information. "
            "DEAP will now abort."), traceback
    else:
        return _stringify(expr)

def evaluateADF(seq):
    """Evaluate a list of ADF and return a dict mapping the ADF name with its
    lambda function.
    """
    adfdict = {}
    for i, expr in enumerate(reversed(seq[1:])):
        func = lambdify(expr.pset, expr)
        adfdict.update({expr.pset.__name__ : func})
        for expr2 in reversed(seq[1:i+1]):
            expr2.pset.functions.update(adfdict)
    return adfdict

def lambdify(pset, expr):
    """Return a lambda function of the expression *expr*.

    .. note::
       This function is a stripped version of the lambdify
       function of sympy0.6.6.
    """
    expr = evaluate(expr)
    args = ",".join(a for a in pset.arguments)
    lstr = "lambda %s: %s" % (args, expr)
    try:
        return eval(lstr, dict(pset.functions))
    except MemoryError:
        _, _, traceback = sys.exc_info()
        raise MemoryError, ("DEAP : Error in tree evaluation :"
        " Python cannot evaluate a tree with a height bigger than 90. "
        "To avoid this problem, you should use bloat control on your "
        "operators. See the DEAP documentation for more information. "
        "DEAP will now abort."), traceback

def lambdifyList(expr):
    """Return a lambda function created from a list of trees. The first 
    element of the list is the main tree, and the following elements are
    automatically defined functions (ADF) that can be called by the first
    tree.
    """
    adfdict = evaluateADF(expr)
    expr[0].pset.functions.update(adfdict)   
    return lambdify(expr[0].pset, expr[0])

## Loosely + Strongly Typed GP 

class Primitive(object):
    """Class that encapsulates a primitive and when called with arguments it
    returns the Python code to call the primitive with the arguments.
        
        >>> import operator
        >>> pr = Primitive(operator.mul, (int, int), int)
        >>> pr("1", "2")
        'mul(1, 2)'
    """    
        
    def __init__(self, primitive, args, ret = __type__):
        self.name = primitive.__name__
        self.arity = len(args)           
        self.args = args
        self.ret = ret
        args = ", ".join(("%s",) * self.arity)
        self.seq = "%s(%s)" % (self.name, args)  
    def __call__(self, *args):
        return self.seq % args  
    def __repr__(self):
        return self.name 

class Operator(Primitive):
    """Class that encapsulates an operator and when called with arguments it
    returns the Python code to call the operator with the arguments. It acts
    as the Primitive class, but instead of returning a function and its 
    arguments, it returns an operator and its operands.
        
        >>> import operator
        >>> op = Operator(operator.mul, (int, int), int)
        >>> op("1", "2")
        '(1 * 2)'
        >>> op2 = Operator(operator.neg, (int,), int)
        >>> op2(1)
        '-(1)'
    """

    symbols = {"add" : "+", "sub" : "-", "mul" : "*", "div" : "/", "neg" : "-",
               "and_" : "and", "or_" : "or", "not_" : "not", 
               "lt" : "<", "eq" : "==", "gt" : ">", "geq" : ">=", "leq" : "<="}
    def __init__(self, operator, args, ret = __type__):
        Primitive.__init__(self, operator, args, ret)
        if len(args) == 1:
            self.seq = "%s(%s)" % (self.symbols[self.name], "%s")
        elif len(args) == 2:
            self.seq = "(%s %s %s)" % ("%s", self.symbols[self.name], "%s")
        else:
            raise ValueError("Operator arity can be either 1 or 2.")

class Terminal(object):
    """Class that encapsulates terminal primitive in expression. Terminals can
    be symbols, values, or 0-arity functions.
    """
    def __init__(self, terminal, ret = __type__):
        self.ret = ret
        try:
            self.value = terminal.__name__
        except AttributeError:
            self.value = terminal
    def __call__(self):
        return self
    def __repr__(self):
        return str(self.value)

class Ephemeral(Terminal):
    """Class that encapsulates a terminal which value is set at run-time.
    The value of the `Ephemeral` can be regenerated by creating a new
    Ephemeral object with the same parameters (func and ret).
    """
    def __init__(self, func, ret = __type__):
        self.func = func
        Terminal.__init__(self, self.func(), ret)
        
class EphemeralGenerator(object):
    """Class that generates `Ephemeral` to be added to an expression."""
    def __init__(self, ephemeral, ret = __type__):
        self.ret = ret
        self.name = ephemeral.__name__
        self.func = ephemeral
    def __call__(self):
        return Ephemeral(self.func, self.ret)
    def __repr__(self):
        return self.name

class PrimitiveSetTyped(object):
    """Class that contains the primitives that can be used to solve a
    Strongly Typed GP problem. The set also defined the researched
    function return type, and input arguments type and number.
    """
    def __init__(self, name, in_types, ret_type, prefix = "ARG"):
        self.terminals = defaultdict(list)
        self.primitives = defaultdict(list)
        self.arguments = []
        self.functions = dict()
        self.terms_count = 0
        self.prims_count = 0
        self.adfs_count = 0
        
        self.__name__ = name 
        self.ret = ret_type
        self.ins = in_types
        for i, type_ in enumerate(in_types):
            self.arguments.append(prefix + ("%s" % i))
            PrimitiveSetTyped.addTerminal(self, self.arguments[-1], type_)
            
    def renameArguments(self, new_args):
        """Rename function arguments with new arguments name *new_args*.
        """
        for i, argument in enumerate(self.arguments):
            if argument in new_args:
                self.arguments[i] = new_args[argument]
        for terminals in self.terminals.itervalues():
            for terminal in terminals:
                if isinstance(terminal, Terminal) and terminal.value in new_args:
                    terminal.value = new_args[terminal.value]

    def addPrimitive(self, primitive, in_types, ret_type):
        """Add a primitive to the set. 

        *primitive* is a callable object or a function.
        *in_types* is a list of argument's types the primitive takes.
        *ret_type* is the type returned by the primitive.
        """
        try:
            prim = Operator(primitive, in_types, ret_type)
        except (KeyError, ValueError):
            prim = Primitive(primitive, in_types, ret_type)
        self.primitives[ret_type].append(prim)
        self.functions[primitive.__name__] = primitive
        self.prims_count += 1
        
    def addTerminal(self, terminal, ret_type):
        """Add a terminal to the set. 

        *terminal* is an object, or a function with no arguments.
        *ret_type* is the type of the terminal.
        """
        if callable(terminal):
            self.functions[terminal.__name__] = terminal
        prim = Terminal(terminal, ret_type)
        self.terminals[ret_type].append(prim)
        self.terms_count += 1
        
    def addEphemeralConstant(self, ephemeral, ret_type):
        """Add an ephemeral constant to the set. An ephemeral constant
        is a no argument function that returns a random value. The value
        of the constant is constant for a Tree, but may differ from one
        Tree to another.

        *ephemeral* function with no arguments that returns a random value.
        *ret_type* is the type of the object returned by the function.
        """
        prim = EphemeralGenerator(ephemeral, ret_type)
        self.terminals[ret_type].append(prim)
        self.terms_count += 1
        
    def addADF(self, adfset):
        """Add an Automatically Defined Function (ADF) to the set.

        *adfset* is a PrimitiveSetTyped containing the primitives with which
        the ADF can be built.        
        """
        prim = Primitive(adfset, adfset.ins, adfset.ret)
        self.primitives[adfset.ret].append(prim)
        self.prims_count += 1
    
    @property
    def terminalRatio(self):
        """Return the ratio of the number of terminals on the number of all
        kind of primitives.
        """
        return self.terms_count / float(self.terms_count + self.prims_count)

class PrimitiveSet(PrimitiveSetTyped):
    """Class same as :class:`~deap.gp.PrimitiveSetTyped`, except there is no 
    definition of type.
    """
    def __init__(self, name, arity, prefix="ARG"):
        args = [__type__]*arity
        PrimitiveSetTyped.__init__(self, name, args, __type__, prefix)

    def addPrimitive(self, primitive, arity):
        """Add primitive *primitive* with arity *arity* to the set."""
        assert arity > 0, "arity should be >= 1"
        args = [__type__] * arity 
        PrimitiveSetTyped.addPrimitive(self, primitive, args, __type__)

    def addTerminal(self, terminal):
        """Add a terminal to the set.""" 
        PrimitiveSetTyped.addTerminal(self, terminal, __type__)

    def addEphemeralConstant(self, ephemeral):
        """Add an ephemeral constant to the set."""
        PrimitiveSetTyped.addEphemeralConstant(self, ephemeral, __type__)

class PrimitiveTree(base.Tree):
    """Tree class faster than base Tree, optimized for Primitives."""
    pset = None   
    
    def _getstate(self):
        state = []
        for elem in self:
            try:
                state.append(elem._getstate())
            except AttributeError:
                state.append(elem)
        return state

    def __deepcopy__(self, memo):
        """Deepcopy a Tree by first converting it back to a list of list.
        
        This deepcopy is faster than the default implementation. From
        quick testing, up to 1.6 times faster, and at least 2 times less
        function calls.
        """
        new = self.__class__(self._getstate())
        new.__dict__.update(copy.deepcopy(self.__dict__, memo))
        return new

# Expression generation functions
def genFull(pset, min_, max_, type_=__type__):
    """Generate an expression where each leaf has a the same depth 
    between *min* and *max*.
    
    :param pset: A primitive set from wich to select primitives of the trees.
    :param min_: Minimum height of the produced trees.
    :param max_: Maximum Height of the produced trees.
    :param type_: The type that should return the tree when called, when
                  :obj:`None` (default) no return type is enforced.
    :returns: A full tree with all leaves at the same depth.
    """
    def condition(height, depth):
        """Expression generation stops when the depth is equal to height."""
        return depth == height
    return generate(pset, min_, max_, condition, type_)

def genGrow(pset, min_, max_, type_=__type__):
    """Generate an expression where each leaf might have a different depth 
    between *min* and *max*.
    
    :param pset: A primitive set from wich to select primitives of the trees.
    :param min_: Minimum height of the produced trees.
    :param max_: Maximum Height of the produced trees.
    :param type_: The type that should return the tree when called, when
                  :obj:`None` (default) no return type is enforced.
    :returns: A grown tree with leaves at possibly different depths.
    """
    def condition(height, depth):
        """Expression generation stops when the depth is equal to height 
        or when it is randomly determined that a a node should be a terminal.
        """
        return depth == height or \
               (depth >= min_ and random.random() < pset.terminalRatio)
    return generate(pset, min_, max_, condition, type_)
    
def genRamped(pset, min_, max_, type_=__type__):
    """Generate an expression with a PrimitiveSet *pset*.
    Half the time, the expression is generated with :func:`~deap.gp.genGrow`,
    the other half, the expression is generated with :func:`~deap.gp.genFull`.
    
    :param pset: A primitive set from wich to select primitives of the trees.
    :param min_: Minimum height of the produced trees.
    :param max_: Maximum Height of the produced trees.
    :param type_: The type that should return the tree when called, when
                  :obj:`None` (default) no return type is enforced.
    :returns: Either, a full or a grown tree.
    """
    method = random.choice((genGrow, genFull))
    return method(pset, min_, max_, type_)

def generate(pset, min_, max_, condition, type_=__type__):
    """Generate a Tree as a list of list. The tree is build
    from the root to the leaves, and it stop growing when the
    condition is fulfilled. 

    :param pset: A primitive set from wich to select primitives of the trees.
    :param min_: Minimum height of the produced trees.
    :param max_: Maximum Height of the produced trees.
    :param condition: The condition is a function that kes two arguments, 
                      the height of the tree to build and the current 
                      depth in the tree.
    :param type_: The type that should return the tree when called, when
                  :obj:`None` (default) no return type is enforced.
    :returns: A grown tree with leaves at possibly different depths 
              dependending on the condition function.
    """
    def genExpr(height, depth, type_):
        if condition(height, depth):
            term = random.choice(pset.terminals[type_])
            expr = term()
        else:
            prim = random.choice(pset.primitives[type_])
            expr = [prim]
            args = (genExpr(height, depth+1, arg) for arg in prim.args)
            expr.extend(args)
        return expr
    height = random.randint(min_, max_)
    expr = genExpr(height, 0, type_)
    if not isinstance(expr, list):
        expr = [expr]
    return expr


######################################
# GP Crossovers                      #
######################################

def cxUniformOnePoint(ind1, ind2):
    """Randomly select in each individual and exchange each subtree with the
    point as root between each individual.
    
    :param ind1: First tree participating in the crossover.
    :param ind2: Second tree participating in the crossover.
    :returns: A tuple of two trees.
    """    
    try:
        index1 = random.randint(1, ind1.size-1)
        index2 = random.randint(1, ind2.size-1)
    except ValueError:
        return ind1, ind2

    sub1 = ind1.searchSubtreeDF(index1)
    sub2 = ind2.searchSubtreeDF(index2)
    ind1.setSubtreeDF(index1, sub2)
    ind2.setSubtreeDF(index2, sub1)
    
    return ind1, ind2
    
## Strongly Typed GP crossovers
def cxTypedOnePoint(ind1, ind2):
    """Randomly select in each individual and exchange each subtree with the 
    point as root between each individual. Since the node are strongly typed, 
    the operator then make sure the type of second node correspond to the type
    of the first node. If it doesn't, it randomly selects another point in the
    second individual and try again. It tries up to *5* times before
    giving up on the crossover.
    
    :param ind1: First typed tree participating in the crossover.
    :param ind2: Second typed tree participating in the crossover.
    :returns: A tuple of two typed trees.
    
    .. note::
       This crossover is subject to change for a more effective method 
       of selecting the crossover points.
    """
    # choose the crossover point in each individual
    try:
        index1 = random.randint(1, ind1.size-1)
        index2 = random.randint(1, ind2.size-1)
    except ValueError:
        return ind1, ind2
        
    subtree1 = ind1.searchSubtreeDF(index1)
    subtree2 = ind2.searchSubtreeDF(index2)

    type1 = subtree1.root.ret
    type2 = subtree2.root.ret 

    # try to mate the trees
    # if no crossover point is found after 5 it gives up trying
    # mating individuals.
    tries = 0
    MAX_TRIES = 5
    while not (type1 == type2) and tries < MAX_TRIES:
        index2 = random.randint(1, ind2.size-1)
        subtree2 = ind2.searchSubtreeDF(index2)
        type2 = subtree2.root.ret
        tries += 1
    
    if type1 == type2:
        sub1 = ind1.searchSubtreeDF(index1)
        sub2 = ind2.searchSubtreeDF(index2)
        ind1.setSubtreeDF(index1, sub2)
        ind2.setSubtreeDF(index2, sub1)
    
    return ind1, ind2


def cxOnePointLeafBiased(ind1, ind2, termpb):
    """Randomly select crossover point in each individual and exchange each
    subtree with the point as root between each individual.
    
    :param ind1: First tree participating in the crossover.
    :param ind2: Second tree participating in the crossover.
    :param termpb: The probability of chosing a terminal node (leaf).
    :returns: A tuple of two trees.
    
    This operator takes another parameter *termpb*, which set the probability
    to choose between a terminal or non-terminal crossover point.
    For instance, as defined by Koza, non-terminal primitives are selected for 
    90% of the crossover points, and terminals for 10%, so *termpb* should be
    set to 0.1.
    """
    size1, size2 = ind1.size, ind2.size

    if size1 == 1 or size2 == 1:
        return ind1, ind2
    
    # Those were not implemented with set because random.choice()
    # works only on sequencable iterables (it is not clear whether
    # it would be faster to perform the conversion set->list or
    # directly use lists)
    termsList1 = [termIndex for termIndex in ind1.iter_leaf_idx]
    termsList2 = [termIndex for termIndex in ind2.iter_leaf_idx]
    primList1 = [i for i in xrange(1, size1) if i not in termsList1]
    primList2 = [i for i in xrange(1, size2) if i not in termsList2]

    if random.random() < termpb or len(primList1) == 0:
        # Choose a terminal from the first parent
        index1 = random.choice(termsList1)
        subtree1 = ind1.searchSubtreeDF(index1)
    else:
        # Choose a primitive (non-terminal) from the first parent
        index1 = random.choice(primList1)
        subtree1 = ind1.searchSubtreeDF(index1)

    if random.random() < termpb or len(primList2) == 0:
        # Choose a terminal from the second parent
        index2 = random.choice(termsList2)
        subtree2 = ind2.searchSubtreeDF(index2)
    else:
        # Choose a primitive (non-terminal) from the second parent
        index2 = random.choice(primList2)
        subtree2 = ind2.searchSubtreeDF(index2)

    ind1.setSubtreeDF(index1, subtree2)
    ind2.setSubtreeDF(index2, subtree1)

    return ind1, ind2

## Strongly Typed GP crossovers
def cxTypedOnePointLeafBiased(ind1, ind2, termpb):
    """Randomly select crossover point in each individual and exchange each
    subtree with the point as root between each individual. 
    
    :param ind1: First typed tree participating in the crossover.
    :param ind2: Second typed tree participating in the crossover.
    :param termpb: The probability of chosing a terminal node (leaf).
    :returns: A tuple of two typed trees.
    
    Since the node are strongly typed, the operator then make sure the type of
    second node correspond to the type of the first node. If it doesn't, it
    randomly selects another point in the second individual and try again. It
    tries up to *5* times before giving up on the crossover.
    
    This operator takes another parameter *termpb*, which set the probability
    to choose between a terminal or non-terminal crossover point. For
    instance, as defined by Koza, non-terminal primitives are selected for 90%
    of the crossover points, and terminals for 10%, so *termpb* should be set
    to 0.1.
    
    .. note::
       This crossover is subject to change for a more effective method
       of selecting the crossover points.
    """
    size1, size2 = ind1.size, ind2.size

    if size1 == 1 or size2 == 1:
        return ind1, ind2

    # Those were not implemented with set because random.choice()
    # works only on sequencable iterables (it is not clear whether
    # it would be faster to perform the conversion set->list or
    # directly use lists)
    termsList1 = [termIndex for termIndex in ind1.iter_leaf_idx]
    termsList2 = [termIndex for termIndex in ind2.iter_leaf_idx]
    primList1 = [i for i in xrange(1, size1) if i not in termsList1]
    primList2 = [i for i in xrange(1, size2) if i not in termsList2]

    if random.random() < termpb or len(primList1) == 0:
        # Choose a terminal from the first parent
        index1 = random.choice(termsList1)
        subtree1 = ind1.searchSubtreeDF(index1)
    else:
        # Choose a primitive (non-terminal) from the first parent
        index1 = random.choice(primList1)
        subtree1 = ind1.searchSubtreeDF(index1)

    if random.random() < termpb or len(primList2) == 0:
        # Choose a terminal from the second parent
        index2 = random.choice(termsList2)
        subtree2 = ind2.searchSubtreeDF(index2)
    else:
        # Choose a primitive (non-terminal) from the second parent
        index2 = random.choice(primList2)
        subtree2 = ind2.searchSubtreeDF(index2)

    type1 = subtree1.root.ret
    type2 = subtree2.root.ret

    # try to mate the trees
    # if no crossover point is found after MAX_CX_TRY
    # the children are returned without modifications.
    tries = 0
    MAX_CX_TRY = 5
    while not (type1 is type2) and tries != MAX_CX_TRY:
        if random.random() < termpb or len(primList2) == 0:
            index2 = random.choice(termsList2)
            subtree2 = ind2.searchSubtreeDF(index2)
        else:
            index2 = random.choice(primList2)
            subtree2 = ind2.searchSubtreeDF(index2)

        type2 = subtree2.root.ret

        tries += 1


    if type1 is type2:
        ind1.setSubtreeDF(index1, subtree2)
        ind2.setSubtreeDF(index2, subtree1)

    return ind1, ind2

######################################
# GP Mutations                       #
######################################
def mutUniform(individual, expr):
    """Randomly select a point in the tree *individual*, then replace the
    subtree at that point as a root by the expression generated using method
    :func:`expr`.
    
    :param individual: The tree to be mutated.
    :param expr: A function object that can generate an expression when
                 called.
    :returns: A tuple of one tree.
    """
    index = random.randint(0, individual.size-1)
    individual.setSubtreeDF(index, expr(pset=individual.pset))
    
    return individual,

## Strongly Typed GP mutations
def mutTypedUniform(individual, expr):
    """The mutation of strongly typed GP expression is pretty easy. First,
    it finds a subtree. Second, it has to identify the return type of the root
    of  this subtree. Third, it generates a new subtree with a root returning
    the required type using function :func:`expr`. Finally, the old
    subtree is replaced by the new subtree.
    
    :param individual: The typed tree to be mutated.
    :param expr: A function object that can generate an expression when
                 called.
    :returns: A tuple of one typed tree.
    """
    index = random.randint(0, individual.size-1)
    subtree = individual.searchSubtreeDF(index)  
    individual.setSubtreeDF(index, expr(pset=individual.pset,
                                        type_=subtree.root.ret))
    
    return individual,


def mutTypedNodeReplacement(individual):
    """Replaces a randomly chosen primitive from *individual* by a randomly
    chosen primitive with the same number of arguments from the :attr:`pset`
    attribute of the individual.
    
    :param individual: The normal or typed tree to be mutated.
    :returns: A tuple of one normal/typed tree.
    
    This operator works on either normal and strongly typed trees.
    """
    if individual.size < 2:
        return individual,

    index = random.randint(1, individual.size-1)
    node = individual.searchSubtreeDF(index)

    if node.size == 1:
        subtree = random.choice(individual.pset.terminals[node.root.ret])()
        individual.setSubtreeDF(index, subtree)

    else:
        # We're going to replace one of the *node* children
        index = random.randint(1, len(node) - 1)
        if node[index].size > 1:
            prim_set = individual.pset.primitives[node[index].root.ret]
            repl_node = random.choice(prim_set)
            while repl_node.args != node[index].root.args:
                repl_node = random.choice(prim_set)
            node[index][0] = repl_node
        else:
            term_set = individual.pset.terminals[node[index].root.ret]
            repl_node = random.choice(term_set)()
            node[index] = repl_node

    return individual,

def mutTypedEphemeral(individual, mode):
    """This operator works on the constants of the tree *individual*. In
    *mode* ``"one"``, it will change the value of one of the individual
    ephemeral constants by calling its generator function. In *mode*
    ``"all"``, it will change the value of **all** the ephemeral constants.
    
    :param individual: The normal or typed tree to be mutated.
    :param mode: A string to indicate to change ``"one"`` or ``"all"``
                 ephemeral constants.
    :returns: A tuple of one normal/typed tree.
    
    This operator works on either normal and strongly typed trees.
    """
    if mode not in ["one", "all"]:
        raise ValueError("Mode must be one of \"one\" or \"all\"")
    ephemerals_idx = []
    for index,node in enumerate(individual.iter):
        if isinstance(node.root.obj, Ephemeral):
            ephemerals_idx.append(index)
    
    if len(ephemerals_idx) > 0:
        if mode == "one":
            ephemerals_idx = (random.choice(ephemerals_idx),)

        for i in ephemerals_idx:
            eph = individual.searchSubtreeDF(i)
            individual.setSubtreeDF(i, Ephemeral(eph.root.func, eph.root.ret))
            
    return individual,

def mutShrink(individual):
    """This operator shrinks the *individual* by chosing randomly a branch and
    replacing it with one of the branch's arguments (also randomly chosen).
    
    :param individual: The tree to be shrinked.
    :returns: A tuple of one tree.
    
    This operator is not suitable for typed tree.
    """
    if individual.size < 3 or individual.height <= 2:
        return individual,       # We don't want to "shrink" the root

    index = random.randint(1, individual.size-2)
    
    # Shrinking a terminal is useless
    while individual.searchSubtreeDF(index).size == 1:
        index = random.randint(1, individual.size-2)

    deleted_node = individual.searchSubtreeDF(index)
    repl_subtree_index = random.randint(1, len(deleted_node)-1)

    individual.setSubtreeDF(index, deleted_node[repl_subtree_index])

    return individual,

def mutTypedInsert(individual):
    """Inserts a new branch at a random position in *individual*. The subtree
    at the chosen position is used as child node of the created subtree, in
    that way, it is really an insertion rather than a replacement. Note that
    the original subtree will become one of the children of the new primitive
    inserted, but not perforce the first (its position is randomly selected if
    the new primitive has more than one child).
    
    :param individual: The normal or typed tree to be mutated.
    :returns: A tuple of one normal/typed tree.
    
    This operator works on either normal and strongly typed trees.
    """
    pset = individual.pset
    index = random.randint(0, individual.size-1)
    node = individual.searchSubtreeDF(index)
    if node.size > 1:     # We do not need to deepcopy the leafs
        node = copy.deepcopy(node)
    
    new_primitive = None
    tries = 0
    MAX_TRIES = 5
    while tries < MAX_TRIES:
        new_primitive = random.choice(pset.primitives[node.root.ret])
        if node.root.ret in new_primitive.args:
            break
        tries += 1
        new_primitive = None

    if new_primitive is None:
        return individual,

    inserted_list = [new_primitive]
    for i in xrange(0, new_primitive.arity):
        # Fill new primitive with random terminals
        new_child = random.choice(pset.terminals[new_primitive.args[i]])
        inserted_list.append(new_child())
    
    # Insert the original tree at a random (but valid) position
    valid_pos = [i for i in xrange(new_primitive.arity) if new_primitive.args[i] == node.root.ret]
    inserted_list[random.choice(valid_pos)+1] = node    # +1 because index 0 is the parent

    individual.setSubtreeDF(index, inserted_list)
    return individual,

if __name__ == "__main__":
    import doctest
    doctest.testmod()
