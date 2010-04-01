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

def evaluate(expr):
    try:
        func = expr[0]
        return func(*[evaluate(value) for value in expr[1:]])
    except TypeError:
        return expr

def generate_ramped(psets, min, max):
    method = random.choice([generate_grow, generate_full])
    return method(psets, min, max)

def generate_full(psets, min, max):
    def condition(max_depth):
        return max_depth == 0
    return _generate(psets, min, max, condition)

def generate_grow(psets, min, max):
    termset_ratio = len(psets.terminals) / \
                    (len(psets.terminals)+len(psets.primitives))
    def condition(max_depth):
        return max_depth == 0 or random.random() < termset_ratio
    return _generate(psets, min, max, condition)

def _generate(psets, min, max, condition):
    def generate_expr(max_depth):
        if condition(max_depth):
            term = random.choice(psets.terminals)
            if not callable(term):
                expr = [term]
            else:
                expr = [term()]
        else:
            func, arity = random.choice(psets.primitives)
            expr = [func]
            for i in xrange(arity):
                arg = generate_expr(max_depth-1)
                if len(arg) > 1:
                    expr.append(arg)
                else:
                    expr.extend(arg)
        return expr
    max_depth = random.randint(min, max)
    return generate_expr(max_depth)

def lambdify(psets, expr, args):
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
    return eval(lstr, psets.func_dict)


class Primitive(object):
    def __init__(self, primitive, arity):
        name = primitive.__name__
        args = ", ".join(repeat("%s",arity))
        self.seq = "%s(%s)" % (name, args)
    def __call__(self, *args):
        return self.seq % args

class ProgrammingSets(object):
    def __init__(self):
        self.primitives = []
        self.terminals = []
        self.func_dict = dict()
        
    def addPrimitive(self, primitive, arity):
        if arity <= 0:
            raise ValueError("arity should be >= 1")
        self.primitives.append((Primitive(primitive,arity), arity))
        self.func_dict[primitive.__name__] = primitive

    def addTerminal(self, terminal):    
        if callable(terminal):
            self.func_dict[terminal.__name__] = terminal
            self.terminals.append(Primitive(terminal,0))
        else:
            self.terminals.append(terminal)

    def addEphemeralConstant(self, ephemeral):
        self.terminals.append(ephemeral)

