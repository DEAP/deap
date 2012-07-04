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
from functools import partial
from operator import eq, lt

######################################
# GP Data structure                  #
######################################

# Define the name of type for any types.
__type__ = None

class PrimitiveTree(list):
    """Tree spefically formated for optimization of genetic 
    programming operations. The tree is represented with a 
    list where the nodes are appended in a depth-first order.
    The nodes appended to the tree are required to define to
    have an attribute *arity* which defines the arity of the
    primitive. An arity of 0 is expected from terminals nodes.
    """
    def __init__(self, content):
        list.__init__(self, content)

    def __deepcopy__(self, memo):
        new = self.__class__(self)
        new.__dict__.update(copy.deepcopy(self.__dict__, memo))
        return new

    @property
    def height(self):
        """Return the height of the tree, or the depth of the
        deepest node.
        """
        stack = [0]
        max_depth = 0
        for elem in self:
            depth = stack.pop()
            max_depth = max(max_depth, depth)
            stack.extend([depth+1] * elem.arity)
        return max_depth

    @property
    def root(self):
        """Root of the tree, the element 0 of the list.
        """
        return self[0]

    def searchSubtree(self, begin):
        """Return a slice object that corresponds to the
        range of values that defines the subtree which has the
        element with index *begin* as its root.
        """
        end = begin + 1
        total = self[begin].arity
        while total > 0:
            total += self[end].arity - 1
            end += 1
        return slice(begin, end)


class Primitive(object):
    """Class that encapsulates a primitive and when called with arguments it
    returns the Python code to call the primitive with the arguments.
        
        >>> import operator
        >>> pr = Primitive(operator.mul, (int, int), int)
        >>> pr.toString("1", "2")
        'mul(1, 2)'
    """    
        
    def __init__(self, primitive, args, ret = __type__):
        self.name = primitive.__name__
        self.arity = len(args)           
        self.args = args
        self.ret = ret
        args = ", ".join(("%s",) * self.arity)
        self.seq = "%s(%s)" % (self.name, args)
    
    def toString(self, *args):
        return self.seq % args

    def __repr__(self):
        return self.name

class Operator(Primitive):
    """Class that encapsulates an operator and when called with arguments it
    returns the Python code to call the operator with the arguments. It acts
    as the Primitive class, but instead of returning a function and its 
    arguments, it returns an operator and its operands.
        
        >>> import operator
        >>> op = Operator(operator.mul, '*', (int, int), int)
        >>> op.toString("1", "2")
        '(1 * 2)'
        >>> op2 = Operator(operator.neg, '-', (int,), int)
        >>> op2.toString(1)
        '-(1)'
    """
    def __init__(self, operator, symbol, args, ret = __type__):
        Primitive.__init__(self, operator, args, ret)
        if len(args) == 1:
            self.seq = "%s(%s)" % (symbol, "%s")
        elif len(args) == 2:
            self.seq = "(%s %s %s)" % ("%s", symbol, "%s")
        else:
            raise ValueError("Operator arity can be either 1 or 2.")

class Terminal(object):
    """Class that encapsulates terminal primitive in expression. Terminals can
    be symbols, values, or 0-arity functions.
    """
    def __init__(self, terminal, ret = __type__):
        self.ret = ret
        self.arity = 0
        try:
            self.value = terminal.__name__
        except AttributeError:
            self.value = terminal
    
    def toString(self):
        return str(self.value)
    
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
        
        self.__name__ = name 
        self.ret = ret_type
        self.ins = in_types
        for i, type_ in enumerate(in_types):
            self.arguments.append(prefix + ("%s" % i))
            PrimitiveSetTyped.addTerminal(self, self.arguments[-1], type_)
            
    def renameArguments(self, **kargs):
        """Rename function arguments with new names from *kargs*.
        """
        for i, argument in enumerate(self.arguments):
            if argument in kargs:
                self.arguments[i] = kargs[argument]
        for terminals in self.terminals.itervalues():
            for terminal in terminals:
                if isinstance(terminal, Terminal) and terminal.value in kargs:
                    terminal.value = kargs[terminal.value]

    def addPrimitive(self, primitive, in_types, ret_type, symbol=None):
        """Add a primitive to the set. 

        *primitive* is a callable object or a function.
        *in_types* is a list of argument's types the primitive takes.
        *ret_type* is the type returned by the primitive.
        """
        if symbol is not None:
            prim = Operator(primitive, symbol, in_types, ret_type)
        else:
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

    def addPrimitive(self, primitive, arity, symbol=None):
        """Add primitive *primitive* with arity *arity* to the set."""
        assert arity > 0, "arity should be >= 1"
        args = [__type__] * arity 
        PrimitiveSetTyped.addPrimitive(self, primitive, args, __type__, symbol)

    def addTerminal(self, terminal):
        """Add a terminal to the set.""" 
        PrimitiveSetTyped.addTerminal(self, terminal, __type__)

    def addEphemeralConstant(self, ephemeral):
        """Add an ephemeral constant to the set."""
        PrimitiveSetTyped.addEphemeralConstant(self, ephemeral, __type__)


######################################
# GP Tree evaluation functions       #
######################################
def stringify(expr):
    """Evaluate the expression *expr* into a string.
    """
    string = ""
    stack = []
    for node in expr:
        stack.append((node, []))
        while len(stack[-1][1]) == stack[-1][0].arity:
            prim, args = stack.pop()
            string = prim.toString(*args)
            if len(stack) == 0:
                break   # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    return string

def evaluate(expr, pset):
    """Evaluate the expression *expr* into Python code object.
    """
    string = stringify(expr)
    try:
        return eval(string, dict(pset.functions))
    except MemoryError:
        _, _, traceback = sys.exc_info()
        raise MemoryError, ("DEAP : Error in tree evaluation :"
        " Python cannot evaluate a tree higher than 90. "
        "To avoid this problem, you should use bloat control on your "
        "operators. See the DEAP documentation for more information. "
        "DEAP will now abort."), traceback

def lambdify(expr, pset):
    """Return a lambda function of the expression *expr*.

    .. note::
       This function is a stripped version of the lambdify
       function of sympy0.6.6.
    """
    string = stringify(expr)
    args = ",".join(arg for arg in pset.arguments)
    lstr = "lambda %s: %s" % (args, string)
    try:
        return eval(lstr, dict(pset.functions))
    except MemoryError:
        _, _, traceback = sys.exc_info()
        raise MemoryError, ("DEAP : Error in tree evaluation :"
        " Python cannot evaluate a tree higher than 90. "
        "To avoid this problem, you should use bloat control on your "
        "operators. See the DEAP documentation for more information. "
        "DEAP will now abort."), traceback

def lambdifyADF(expr):
    """Return a lambda function created from a list of trees. The first 
    element of the list is the main tree, and the following elements are
    automatically defined functions (ADF) that can be called by the first
    tree.
    """
    adfdict = {}
    func = None
    for subexpr in reversed(expr):
        subexpr.pset.functions.update(adfdict)
        func = lambdify(subexpr, subexpr.pset)
        adfdict.update({subexpr.pset.__name__ : func})
    return func

######################################
# GP Program generation functions    #
######################################
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
    :param condition: The condition is a function that takes two arguments,
                      the height of the tree to build and the current
                      depth in the tree.
    :param type_: The type that should return the tree when called, when
                  :obj:`None` (default) no return type is enforced.
    :returns: A grown tree with leaves at possibly different depths
              dependending on the condition function.
    """
    expr = []
    height = random.randint(min_, max_)
    stack = [(0, type_)]
    while len(stack) != 0:
        depth, type_ = stack.pop()
        if condition(height, depth):
            term = random.choice(pset.terminals[type_])
            if isinstance(term, EphemeralGenerator):
                term = term()
            expr.append(term)
        else:
            prim = random.choice(pset.primitives[type_])
            expr.append(prim)
            for arg in prim.args:
                stack.append((depth+1, arg))
    return expr


######################################
# GP Crossovers                      #
######################################

def cxOnePoint(ind1, ind2):
    """Randomly select in each individual and exchange each subtree with the
    point as root between each individual.
    
    :param ind1: First tree participating in the crossover.
    :param ind2: Second tree participating in the crossover.
    :returns: A tuple of two trees.
    """
    if len(ind1) < 2 or len(ind2) < 2:
        # No crossover on single node tree
        return ind1, ind2
    
    # List all available primitive types in each individual
    types1 = defaultdict(list)
    types2 = defaultdict(list)    
    if ind1.root.ret == __type__:
        # Not STGP optimization
        types1[__type__] = xrange(1, len(ind1))
        types2[__type__] = xrange(1, len(ind2))
        common_types = [__type__]
    else:
        for idx, node in enumerate(ind1[1:], 1):
            types1[node.ret].append(idx)
        for idx, node in enumerate(ind2[1:], 1):
            types2[node.ret].append(idx)
        common_types = set(types1.keys()).intersection(set(types2.keys()))
    
    if len(common_types) > 0:
        type_ = random.choice(list(common_types))
        
        index1 = random.choice(types1[type_])
        index2 = random.choice(types2[type_])

        slice1 = ind1.searchSubtree(index1)
        slice2 = ind2.searchSubtree(index2)
        ind1[slice1], ind2[slice2] = ind2[slice2], ind1[slice1]
    
    return ind1, ind2


def cxOnePointLeafBiased(ind1, ind2, termpb):
    """Randomly select crossover point in each individual and exchange each
    subtree with the point as root between each individual. 
    
    :param ind1: First typed tree participating in the crossover.
    :param ind2: Second typed tree participating in the crossover.
    :param termpb: The probability of chosing a terminal node (leaf).
    :returns: A tuple of two typed trees.
    
    When the nodes are strongly typed, the operator makes sure the
    second node type corresponds to the first node type.
    
    The parameter *termpb* sets the probability to choose between a terminal
    or non-terminal crossover point. For instance, as defined by Koza, non-
    terminal primitives are selected for 90% of the crossover points, and
    terminals for 10%, so *termpb* should be set to 0.1.
    """

    if len(ind1) < 2 or len(ind2) < 2:
        # No crossover on single node tree
        return ind1, ind2
    
    # Determine wether we keep terminals or primitives for each individual
    terminal_op = partial(eq, 0)
    primitive_op = partial(lt, 0)
    arity_op1 = terminal_op if random.random() < termpb else primitive_op
    arity_op2 = terminal_op if random.random() < termpb else primitive_op

    # List all available primitive or terminal types in each individual
    types1 = defaultdict(list)
    types2 = defaultdict(list)

    for idx, node in enumerate(ind1[1:], 1):
        if arity_op1(node.arity):
            types1[node.ret].append(idx)

    for idx, node in enumerate(ind2[1:], 1):
        if arity_op2(node.arity):
            types2[node.ret].append(idx)

    common_types = set(types1.keys()).intersection(set(types2.keys()))
    
    if len(common_types) > 0:
        # Set does not support indexing
        type_ = random.sample(common_types, 1)[0]
        index1 = random.choice(types1[type_])
        index2 = random.choice(types2[type_])

        slice1 = ind1.searchSubtree(index1)
        slice2 = ind2.searchSubtree(index2)
        ind1[slice1], ind2[slice2] = ind2[slice2], ind1[slice1]

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
    index = random.randrange(len(individual))
    slice_ = individual.searchSubtree(index)
    type_ = individual[index].ret
    individual[slice_] = expr(pset=individual.pset, type_=type_)
    return individual,


def mutNodeReplacement(individual):
    """Replaces a randomly chosen primitive from *individual* by a randomly
    chosen primitive with the same number of arguments from the :attr:`pset`
    attribute of the individual.
    
    :param individual: The normal or typed tree to be mutated.
    :returns: A tuple of one tree.
    """
    if len(individual) < 2:
        return individual,

    index = random.randrange(1, len(individual))
    node = individual[index]
    pset = individual.pset

    if node.arity == 0: # Terminal
        term = random.choice(pset.terminals[node.ret])
        if isinstance(term, EphemeralGenerator):
            term = term()
        individual[index] = term 
    else:   # Primitive
        prims = [p for p in pset.primitives[node.ret] if p.args == node.args]
        individual[index] = random.choice(prims)

    return individual,

def mutEphemeral(individual, mode):
    """This operator works on the constants of the tree *individual*. In
    *mode* ``"one"``, it will change the value of one of the individual
    ephemeral constants by calling its generator function. In *mode*
    ``"all"``, it will change the value of **all** the ephemeral constants.
    
    :param individual: The normal or typed tree to be mutated.
    :param mode: A string to indicate to change ``"one"`` or ``"all"``
                 ephemeral constants.
    :returns: A tuple of one tree.
    """
    if mode not in ["one", "all"]:
        raise ValueError("Mode must be one of \"one\" or \"all\"")
    ephemerals_idx = []
    for index, node in enumerate(individual):
        if isinstance(node, Ephemeral):
            ephemerals_idx.append(index)
    
    if len(ephemerals_idx) > 0:
        if mode == "one":
            ephemerals_idx = (random.choice(ephemerals_idx),)

        for i in ephemerals_idx:
            eph = individual[i]
            individual[i] =  Ephemeral(eph.func, eph.ret)
            
    return individual,

def mutInsert(individual):
    """Inserts a new branch at a random position in *individual*. The subtree
    at the chosen position is used as child node of the created subtree, in
    that way, it is really an insertion rather than a replacement. Note that
    the original subtree will become one of the children of the new primitive
    inserted, but not perforce the first (its position is randomly selected if
    the new primitive has more than one child).
    
    :param individual: The normal or typed tree to be mutated.
    :returns: A tuple of one tree.
    """
    pset = individual.pset
    index = random.randrange(len(individual))
    node = individual[index]
    slice_ = individual.searchSubtree(index)
    choice = random.choice
    
    # As we want to keep the current node as children of the new one,
    # it must accept the return value of the current node
    primitives = [p for p in pset.primitives[node.ret] if node.ret in p.args]
    
    if len(primitives) == 0:
        return individual,
    
    new_node = choice(primitives)
    new_subtree = [None] * len(new_node.args)
    position = choice([i for i, a in enumerate(new_node.args) if a == node.ret])
    
    for i, arg_type in enumerate(new_node.args):
        if i != position:
            term = choice(pset.terminals[arg_type])
            if isinstance(term, EphemeralGenerator):
                term = term()            
            new_subtree[i] = term
    
    new_subtree[position:position+1] = individual[slice_]
    new_subtree.insert(0, new_node)
    individual[slice_] = new_subtree
    return individual,


######################################
# GP bloat control decorators        #
######################################   

def staticDepthLimit(max_depth):
    """Implement a static limit on the depth of a GP tree, as defined by Koza
    in [Koza1989]. It may be used to decorate both crossover and mutation
    operators. When an invalid (too high) child is generated, it is simply
    replaced by one of its parents.
    
    This operator can be used to avoid memory errors occuring when the tree
    gets higher than 90-95 levels (as Python puts a limit on the call stack
    depth), because it ensures that no tree higher than *max_depth* will ever
    be accepted in the population (except if it was generated at initialization
    time).
    
    .. note::
       If you want to reproduce the exact behavior intended by Koza, set
       the *max_depth* param to 17.
       
    :param max_depth: The maximum depth allowed for an individual
    :returns: A decorator that can be applied to a GP operator using 
    :method:`~deap.tools.Toolbox.decorate`
    
    .. [Koza1989] J.R. Koza, Genetic Programming - On the Programming of 
        Computers by Means of Natural Selection (MIT Press, 
        Cambridge, MA, 1992)

    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            keep_inds = [copy.deepcopy(ind) for ind in args]
            new_inds = list(func(*args, **kwargs))
            for i, ind in enumerate(new_inds):
                if ind.height > max_depth:
                    new_inds[i] = random.choice(keep_inds)
            return new_inds
        return wrapper
    return decorator
    
def staticSizeLimit(max_size):
    """Implement a static limit on the size of a GP tree. It may be used to
    decorate both crossover and mutation operators. When an invalid (too big)
    child is generated, it is simply replaced by one of its parents.
    
    :param max_size: The maximum size (number of nodes) allowed for an 
    individual
    :returns: A decorator that can be applied to a GP operator using 
    :method:`~deap.tools.Toolbox.decorate`
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            keep_inds = [copy.deepcopy(ind) for ind in args]
            new_inds = list(func(*args, **kwargs))
            for i, ind in enumerate(new_inds):
                if len(ind) > max_size:
                    new_inds[i] = random.choice(keep_inds)
            return new_inds
        return wrapper
    return decorator

if __name__ == "__main__":
    import doctest
    doctest.testmod()
