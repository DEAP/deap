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


def lambdify(pset, expr, args):
    """ 
    Returns a lambda function of the expression

    Remark:
    This function is a stripped version of the lambdify
    function of sympy0.6.6.
    """
    if isinstance(expr, list):
        expr = evaluate(expr)
    if isinstance(args, str):
        pass
    elif hasattr(args, "__iter__"):
        args = ",".join(str(a) for a in args)
    else:
        args = str(args)
    lstr = "lambda %s: (%s)" % (args, expr)
    return eval(lstr, pset.func_dict)

## Loosely + Strongly Typed GP 

class Primitive(object):
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
    def __init__(self, func, ret = __type__):
        self.ret = ret
        self.func = func
        Terminal.__init__(self, self.func(), self.ret)
    def regen(self):
        self.value = self.func()
        
class EphemeralGenerator(object):
    def __init__(self, ephemeral, ret = __type__):
        self.ret = ret
        self.name = ephemeral.__name__
        self.func = ephemeral
    def __call__(self):
        return Ephemeral(self.func, self.ret)
    def __repr__(self):
        return self.name

class PrimitiveSetTyped(object):
    def __init__(self):
        self.terminals = defaultdict(list)
        self.primitives = defaultdict(list)
        self.func_dict = dict()
    
    def addPrimitive(self, primitive, in_types, ret_type):
        try:
            prim = Operator(primitive, in_types, ret_type)
        except (KeyError, ValueError):
            prim = Primitive(primitive, in_types, ret_type)
        self.primitives[ret_type].append(prim)
        self.func_dict[primitive.__name__] = primitive
        
    def addTerminal(self, terminal, ret_type):
        if callable(terminal):
            self.func_dict[terminal.__name__] = terminal
        prim = Terminal(terminal, ret_type)
        self.terminals[ret_type].append(prim)
        
    def addEphemeralConstant(self, ephemeral, ret_type):
        prim = EphemeralGenerator(ephemeral, ret_type)
        self.terminals[ret_type].append(prim)

class PrimitiveSet(PrimitiveSetTyped):
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
    termset_ratio = len(pset.terminals) / \
                    (len(pset.terminals)+len(pset.primitives))
    def condition(max_depth):
        return max_depth == 0 or random.random() < termset_ratio
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

