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

import base

from itertools import repeat
from collections import defaultdict

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
            return eval(_stringify(expr), pset.func_dict)
        except MemoryError:
            raise MemoryError,("DEAP : Error in tree evaluation :"
            " Python cannot evaluate a tree with a height bigger than 90. "
            "To avoid this problem, you should use bloat control on your "
            "operators. See the DEAP documentation for more information. "
            "DEAP will now abort.")
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
            expr2.pset.func_dict.update(adfdict)
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
        return eval(lstr, dict(pset.func_dict))
    except MemoryError:
        raise MemoryError,("DEAP : Error in tree evaluation :"
        " Python cannot evaluate a tree with a height bigger than 90. "
        "To avoid this problem, you should use bloat control on your "
        "operators. See the DEAP documentation for more information. "
        "DEAP will now abort.")

def lambdifyList(expr):
    """Return a lambda function created from a list of trees. The first 
    element of the list is the main tree, and the following elements are
    automatically defined functions (ADF) that can be called by the first
    tree.
    """
    adfdict = evaluateADF(expr)
    expr[0].pset.func_dict.update(adfdict)   
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
        args = ", ".join(repeat("%s", self.arity))
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
    The value of the `Ephemeral` can be regenerated with the method `regen`.
    """
    def __init__(self, func, ret = __type__):
        self.func = func
        Terminal.__init__(self, self.func(), ret)
    def regen(self):
        """Regenerate the ephemeral value."""
        self.value = self.func()
        
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
        self.func_dict = dict()
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
            if new_args.has_key(argument):
                self.arguments[i] = new_args[argument]
        for terminals in self.terminals.values():
            for terminal in terminals:
                if ( isinstance(terminal, Terminal) and 
                     new_args.has_key(terminal.value) ):
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
        self.func_dict[primitive.__name__] = primitive
        self.prims_count += 1
        
    def addTerminal(self, terminal, ret_type):
        """Add a terminal to the set. 

        *terminal* is an object, or a function with no arguments.
        *ret_type* is the type of the terminal.
        """
        if callable(terminal):
            self.func_dict[terminal.__name__] = terminal
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
    """
    def condition(max_depth):
        """Expression generation stops when the depth is zero."""
        return max_depth == 0
    return _generate(pset, min_, max_, condition, type_)

def genGrow(pset, min_, max_, type_=__type__):
    """Generate an expression where each leaf might have a different depth 
    between *min* and *max*.
    """
    def condition(max_depth):
        """Expression generation stops when the depth is zero or when
        it is randomly determined that a a node should be a terminal.
        """
        return max_depth == 0 or random.random() < pset.terminalRatio
    return _generate(pset, min_, max_, condition, type_)
    
def genRamped(pset, min_, max_, type_=__type__):
    """Generate an expression with a PrimitiveSet *pset*.
    Half the time, the expression is generated with :func:`~deap.gp.genGrow`,
    the other half, the expression is generated with :func:`~deap.gp.genFull`.
    """
    method = random.choice((genGrow, genFull))
    return method(pset, min_, max_, type_)

def _generate(pset, min_, max_, condition, type_=__type__):
    def genExpr(max_depth, type_):
        if condition(max_depth):
            term = random.choice(pset.terminals[type_])
            expr = term()
        else:
            prim = random.choice(pset.primitives[type_])
            expr = [prim]
            args = (genExpr(max_depth-1, arg) for arg in prim.args)
            expr.extend(args)
        return expr
    max_depth = random.randint(min_, max_)
    expr = genExpr(max_depth, type_)
    if not isinstance(expr, list):
        expr = [expr]
    return expr


######################################
# GP Crossovers                      #
######################################

def cxUniformOnePoint(ind1, ind2):
    """Randomly select in each individual and exchange each subtree with the
    point as root between each individual.
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


def cxOnePointLeafBiased(ind1, ind2, cxtermpb):
    """Randomly select crossover point in each individual and exchange each
    subtree with the point as root between each individual.
    
    This operator takes another parameter *cxtermpb*, which set the probability
    to choose between a terminal or non-terminal crossover point.
    For instance, as defined by Koza, non-terminal primitives are selected for 
    90% of the crossover points, and terminals for 10%, so *cxtermpb* should be
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

    if random.random() < cxtermpb or len(primList1) == 0:
        # Choose a terminal from the first parent
        index1 = random.choice(termsList1)
        subtree1 = ind1.searchSubtreeDF(index1)
    else:
        # Choose a primitive (non-terminal) from the first parent
        index1 = random.choice(primList1)
        subtree1 = ind1.searchSubtreeDF(index1)

    if random.random() < cxtermpb or len(primList2) == 0:
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
def cxTypedOnePointLeafBiased(ind1, ind2, cxtermpb):
    """Randomly select crossover point in each individual and exchange each
    subtree with the point as root between each individual. Since the node are 
    strongly typed, the operator then make sure the type of second node 
    correspond to the type of the first node. If it doesn't, it randomly 
    selects another point in the second individual and try again. It tries up
    to *5* times before giving up on the crossover.
    
    This operator takes another parameter *cxtermpb*, which set the probability
    to choose between a terminal or non-terminal crossover point.
    For instance, as defined by Koza, non-terminal primitives are selected for 
    90% of the crossover points, and terminals for 10%, so *cxtermpb* should be
    set to 0.1.
    
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

    if random.random() < cxtermpb or len(primList1) == 0:
        # Choose a terminal from the first parent
        index1 = random.choice(termsList1)
        subtree1 = ind1.searchSubtreeDF(index1)
    else:
        # Choose a primitive (non-terminal) from the first parent
        index1 = random.choice(primList1)
        subtree1 = ind1.searchSubtreeDF(index1)

    if random.random() < cxtermpb or len(primList2) == 0:
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
        if random.random() < cxtermpb or len(primList2) == 0:
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
    """Randomly select a point in the Tree, then replace the subtree with
    the point as a root by a randomly generated expression. The expression
    is generated using the method `expr`.
    """
    index = random.randint(0, individual.size-1)
    individual.setSubtreeDF(index, expr(pset=individual.pset))
    
    return individual,

## Strongly Typed GP mutations
def mutTypedUniform(individual, expr):
    """The mutation of strongly typed GP expression is pretty easy. First,
    it finds a subtree. Second, it has to identify the return type of the root
    of  this subtree. Third, it generates a new subtree with a root's type
    corresponding to the original subtree root's type. Finally, the old
    subtree is replaced by the new subtree.
    """
    index = random.randint(0, individual.size-1)
    subtree = individual.searchSubtreeDF(index)  
    individual.setSubtreeDF(index, expr(pset=individual.pset,
                                        type_=subtree.root.ret))
    
    return individual,


def mutTypedNodeReplacement(individual):
    """This operator mutates the individual *individual* that are subjected to
    it. The operator randomly chooses a primitive in the individual
    and replaces it with a randomly selected primitive in *pset* that takes
    the same number of arguments.

    This operator works on strongly typed trees as on normal GP trees.
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
    """This operator works on the constants of the tree *ind*.
    In  *mode* ``"one"``, it will change the value of **one**
    of the individual ephemeral constants by calling its generator function.
    In  *mode* ``"all"``, it will change the value of **all**
    the ephemeral constants.

    This operator works on strongly typed trees as on normal GP trees.
    """
    if mode not in ["one", "all"]:
        raise ValueError("Mode must be one of \"one\" or \"all\"")
    ephemerals = []
    for i in xrange(1, individual.size):
        subtree = individual.searchSubtreeDF(i)
        if hasattr(subtree.root.obj, 'regen'):
            ephemerals.append(i)

    if len(ephemerals) > 0:
        if mode == "one":
            ephemerals = [random.choice(ephemerals)]
        elif mode == "all":
            pass

        for i in ephemerals:
            individual.searchSubtreeDF(i).regen()
            
    return individual,

def mutShrink(individual):
    """This operator shrinks the individual *individual* that are subjected to
    it. The operator randomly chooses a branch in the individual and replaces
    it with one of the branch's arguments (also randomly chosen).

    This operator is not usable with STGP.
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
    """This operator mutate the GP tree of the *individual* passed by inserting
    a new branch at a random position in a
    tree, using the original subtree at this position as one argument,
    and if necessary randomly selecting terminal primitives
    to complete the arguments of the inserted node.
    Note that the original subtree will become one of the children of the new
    primitive inserted, but not perforce the first (its position is
    randomly selected if the new primitive has more than one child)

    This operator works on strongly typed trees as on normal GP trees.
    """
    pset = individual.pset
    index = random.randint(0, individual.size-1)
    node = individual.searchSubtreeDF(index)
    if node.size > 1:     # We do not need to deepcopy the leafs
        node = copy.deepcopy(node)
    
    new_primitive = None
    while new_primitive is None or not node.root.ret in new_primitive.args:
        new_primitive = random.choice(pset.primitives[node.root.ret])
    
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
