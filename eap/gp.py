#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

import random
from itertools import repeat
from collections import defaultdict

# Define the name of type for any types.
__type__ = None

## GP Tree utility functions

def evaluate(expr, pset=None):
    """Evaluate the expression expr into a string if pset is None
    or into Python code is pset is not None.
    """
    def _stringify(expr):
        try:
            func = expr[0]
            return str(func(*[_stringify(value) for value in expr[1:]]))
        except TypeError:
            return str(expr)
    if not pset is None:
        return eval(_stringify(expr), pset.func_dict)
    else:
        return _stringify(expr)

def evaluateADF(seq):
    """ Evaluate a list of ADF and return a dict mapping the ADF name with its
        lambda function.
    """
    adfdict = {}
    for i, expr in enumerate(reversed(seq[1:])):
        func = lambdify(expr.pset, expr)
        adfdict.update({expr.pset.name : func})
        for expr2 in reversed(seq[1:i+1]):
            expr2.pset.func_dict.update(adfdict)
            
    return adfdict

def lambdify(pset, expr):
    """Return a lambda function of the expression.

    Remark:
    This function is a stripped version of the lambdify
    function of sympy0.6.6.
    """
    expr = evaluate(expr)
    args = ",".join(a for a in pset.arguments)
    lstr = "lambda %s: (%s)" % (args, expr)
    return eval(lstr, dict(pset.func_dict))

def lambdifyList(expr):
    """ Return a lambda function created from a list of trees. The first 
        element of the list is the main tree, and the following elements are
        automatically defined functions (ADF) that can be called by the first
        tree.
    """
    adfdict = evaluateADF(expr)
    expr[0].pset.func_dict.update(adfdict)   
    return lambdify(expr[0].pset, expr[0])

## Loosely + Strongly Typed GP 

class Primitive(object):
    """ Class that encapsulates a primitive and when called with arguments it
        returns the Python code to call the primitive with the arguments.
        
        >>> import operator
        >>> pr = Primitive(operator.mul, (int, int), int)
        >>> pr("1", "2")
        'mul(1, 2)'
    """    
        
    def __init__(self, primitive, args, ret = __type__):
        self.name = primitive
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
    """ Class that encapsulates an operator and when called with arguments it
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
    """ Class that encapsulates terminal primitive in expression. Terminals can
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
    """ Class that encapsulates a terminal which value is set at run-time. 
        The value of the `Ephemeral` can be regenerated with the method `regen`.
    """
    def __init__(self, func, ret = __type__):
        self.func = func
        Terminal.__init__(self, self.func(), ret)
    def regen(self):
        self.value = self.func()
        
class EphemeralGenerator(object):
    """ Class that generates `Ephemeral` to be added to an expression.
    """
    def __init__(self, ephemeral, ret = __type__):
        self.ret = ret
        self.name = ephemeral.__name__
        self.func = ephemeral
    def __call__(self):
        return Ephemeral(self.func, self.ret)
    def __repr__(self):
        return self.name

class PrimitiveSetTyped(object):
    def __init__(self, name, in_types, ret_type, prefix = "ARG"):
        self.terminals = defaultdict(list)
        self.primitives = defaultdict(list)
        self.arguments = []
        self.func_dict = dict()
        self.terms_count = 0
        self.prims_count = 0
        self.adfs_count = 0
        
        self.name = name 
        self.ret = ret_type
        self.ins = in_types
        for i, type in enumerate(in_types):
            self.arguments.append(prefix + ("%s" % i))
            PrimitiveSetTyped.addTerminal(self, self.arguments[-1], type)
            
    def renameArguments(self, new_args):
        for i, argument in enumerate(self.arguments):
            if new_args.has_key(argument):
                self.arguments[i] = new_args[argument]
        for terminals in self.terminals.values():
            for terminal in terminals:
                if ( isinstance(terminal, Terminal) and 
                     new_args.has_key(terminal.value) ):
                    terminal.value = new_args[terminal.value]

    def addPrimitive(self, primitive, in_types, ret_type):
        try:
            prim = Operator(primitive.__name__, in_types, ret_type)
        except (KeyError, ValueError):
            prim = Primitive(primitive.__name__, in_types, ret_type)
        self.primitives[ret_type].append(prim)
        self.func_dict[primitive.__name__] = primitive
        self.prims_count += 1
        
    def addTerminal(self, terminal, ret_type):
        if callable(terminal):
            self.func_dict[terminal.__name__] = terminal
        prim = Terminal(terminal, ret_type)
        self.terminals[ret_type].append(prim)
        self.terms_count += 1
        
    def addEphemeralConstant(self, ephemeral, ret_type):
        prim = EphemeralGenerator(ephemeral, ret_type)
        self.terminals[ret_type].append(prim)
        self.terms_count += 1
        
    def addADF(self, adfset):
        prim = Primitive(adfset.name, adfset.ins, adfset.ret)
        self.primitives[adfset.ret].append(prim)
    
    @property
    def terminalRatio(self):
        """ Return the ratio of the number of terminals on the number of all
            kinds of primitives.
        """
        return self.terms_count / float(self.terms_count + self.prims_count)

class PrimitiveSet(PrimitiveSetTyped):
    def __init__(self, name, arity, prefix="ARG"):
        args = [__type__]*arity
        PrimitiveSetTyped.__init__(self, name, args, __type__, prefix)

    def addPrimitive(self, primitive, arity):
        assert arity > 0, "arity should be >= 1"
        args = [__type__] * arity 
        PrimitiveSetTyped.addPrimitive(self, primitive, args, __type__)

    def addTerminal(self, terminal):    
        PrimitiveSetTyped.addTerminal(self, terminal, __type__)

    def addEphemeralConstant(self, ephemeral):
        PrimitiveSetTyped.addEphemeralConstant(self, ephemeral, __type__)
        
# Expression generation functions

def generate_ramped(pset, min, max, type=__type__):
    method = random.choice([generate_grow, generate_full])
    return method(pset, min, max, type)

def generate_full(pset, min, max, type=__type__):
    def condition(max_depth):
        return max_depth == 0
    return _generate(pset, min, max, condition, type)

def generate_grow(pset, min, max, type=__type__):
    def condition(max_depth):
        return max_depth == 0 or random.random() < pset.terminalRatio
    return _generate(pset, min, max, condition, type)

def _generate(pset, min, max, condition, type=__type__):
    def generate_expr(max_depth, type):
        if condition(max_depth):
            term = random.choice(pset.terminals[type])
            expr = term()
        else:
            prim = random.choice(pset.primitives[type])
            expr = [prim]
            args = (generate_expr(max_depth-1, arg) for arg in prim.args)
            expr.extend(args)
        return expr
    max_depth = random.randint(min, max)
    expr = generate_expr(max_depth, type)
    if not isinstance(expr, list):
        expr = [expr]
    return expr

if __name__ == "__main__":
    import doctest
    doctest.testmod()

