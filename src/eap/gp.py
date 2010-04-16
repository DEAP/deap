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

## GP Tree utility functions

def evaluate(expr):
    try:
        func = expr[0]
        return func(*[evaluate(value) for value in expr[1:]])
    except TypeError:
        return expr

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

## Normal GP

class Primitive(object):
    def __init__(self, primitive, arity):
        self.arity = arity
        self.name = primitive.__name__
        args = ", ".join(repeat("%s",arity))
        self.seq = "%s(%s)" % (self.name, args)         
    def __call__(self, *args):
        return self.seq % args     
    def __repr__(self):
        return self.name        
        
class Terminal(object):
    def __init__(self, primitive):
        self.name = str(primitive)
    def __call__(self):
        return self        
    def __repr__(self):
        return self.name        

class Ephemeral(object):
    def __init__(self, ephemeral):
       self.name = str(ephemeral)
       self.func = ephemeral
    def __call__(self):
       return Terminal(self.func())
    def __repr__(self):
        return self.name       
       
class PrimitiveSet(object):
    def __init__(self):
        self.primitives = []
        self.terminals = []
        self.func_dict = dict()
        
    def addPrimitive(self, primitive, arity):
        if arity <= 0:
            raise ValueError("arity should be >= 1")
        self.primitives.append(Primitive(primitive,arity))
        self.func_dict[primitive.__name__] = primitive

    def addTerminal(self, terminal):    
        if callable(terminal):
            self.func_dict[terminal.__name__] = terminal
            self.terminals.append(Primitive(terminal,0))
        else:
            self.terminals.append(Terminal(terminal))

    def addEphemeralConstant(self, ephemeral):
        self.terminals.append(Ephemeral(ephemeral))       

## Standard GP generation functions

def generate_ramped(pset, min, max):
    method = random.choice([generate_grow, generate_full])
    return method(pset, min, max)

def generate_full(pset, min, max):
    def condition(max_depth):
        return max_depth == 0
    return _generate(pset, min, max, condition)

def generate_grow(pset, min, max):
    termset_ratio = len(pset.terminals) / \
                    (len(pset.terminals)+len(pset.primitives))
    def condition(max_depth):
        return max_depth == 0 or random.random() < termset_ratio
    return _generate(pset, min, max, condition)

def _generate(pset, min, max, condition):
    def generate_expr(max_depth):
        if condition(max_depth):
            term = random.choice(pset.terminals)
            expr = [term()]
        else:
            prim = random.choice(pset.primitives)
            expr = [prim]
            for i in xrange(prim.arity):
                arg = generate_expr(max_depth-1)
                if len(arg) > 1:
                    expr.append(arg)
                else:
                    expr.extend(arg)
        return expr
    max_depth = random.randint(min, max)
    return generate_expr(max_depth)

## Strongly Typed GP 

class PrimitiveTyped(Primitive):
    def __init__(self, primitive, ret, args):
        self.ret = ret
        self.args = args
        Primitive.__init__(self, primitive, len(args))
        
class TerminalTyped(Terminal):
    def __init__(self, terminal, ret):
        self.ret = ret
        Terminal.__init__(self, terminal)
    def __call__(self):
        return self

class EphemeralTyped(Ephemeral):
    def __init__(self, ephemeral, ret):
        self.ret = ret
        Ephemeral.__init__(self, ephemeral)
    def __call__(self):
        return TerminalTyped(self.func(), self.ret)

class TypedPrimitiveSet(object):
    def __init__(self):
        self.terminals = dict()
        self.primitives = dict()
        self.func_dict = dict()
    
    def addPrimitive(self, primitive, ret_type, in_types):
        if not self.primitives.has_key(ret_type):
           self.primitives[ret_type] = list()
        prim = PrimitiveTyped(primitive, ret_type, in_types)
        self.primitives[ret_type].append(prim)
        self.func_dict[primitive.__name__] = primitive
        
    def addTerminal(self, terminal, ret_type):
        if not self.terminals.has_key(ret_type):
           self.terminals[ret_type] = list()
               
        if callable(terminal):
            self.func_dict[terminal.__name__] = terminal
            prim = PrimitiveTyped(terminal, ret_type, [])
        else:
           prim = TerminalTyped(terminal, ret_type)
        self.terminals[ret_type].append(prim)
        
    def addEphemeralConstant(self, ephemeral, ret_type):
        if not self.terminals.has_key(ret_type):
           self.terminals[ret_type] = list()
        prim = EphemeralTyped(ephemeral, ret_type)
        self.terminals[ret_type].append(prim)

# Strongly Typed GP generation functions

def generate_ramped_typed(pset, type, min, max):
    method = random.choice([generate_grow_typed, generate_full_typed])
    return method(pset, type, min, max)

def generate_full_typed(pset, type, min, max):
    def condition(max_depth):
        return max_depth == 0
    return _generate_typed(pset, type, min, max, condition)

def generate_grow_typed(pset, type, min, max):
    termset_ratio = len(pset.terminals) / \
                    (len(pset.terminals)+len(pset.primitives))
    def condition(max_depth):
        return max_depth == 0 or random.random() < termset_ratio
    return _generate_typed(pset, type, min, max, condition)

def _generate_typed(pset, type, min, max, condition):
    def generate_expr(max_depth, type):
        if condition(max_depth):
            term = random.choice(pset.terminals[type])
            expr = [term()]                
        else:
            prim = random.choice(pset.primitives[type])
            expr = [prim]
            for arg_type in prim.args:
                arg = generate_expr(max_depth-1, arg_type)
                if len(arg) > 1:
                    expr.append(arg)
                else:
                    expr.extend(arg)
        return expr
    max_depth = random.randint(min, max)
    return generate_expr(max_depth, type)


