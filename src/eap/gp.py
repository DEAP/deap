import random
from itertools import repeat

def evaluate(expr):
    try:
        func = expr[0]
        return func(*[evaluate(value) for value in expr[1:]])
    except TypeError:
        return expr

class Primitive(object):
    def __init__(self, primitive, arity):
        name = primitive.__name__
        args = ", ".join(repeat("%s",arity))
        self.seq = "%s(%s)" % (name, args)
    def __call__(self, *args):
        return self.seq % args

class ProgramGenerator(object):
    def __init__(self):
        self.primitive_set = []
        self.terminal_set = []
        self.func_dict = dict()
        
    def addPrimitive(self, primitive, arity):
        if arity <= 0:
            raise ValueError("arity should be >= 1")
        self.primitive_set.append((Primitive(primitive,arity), arity))
        self.func_dict[primitive.__name__] = primitive

    def addTerminal(self, terminal):    
        if callable(terminal):
            self.func_dict[terminal.__name__] = terminal
            self.terminal_set.append(Primitive(terminal,0))
        else:
            self.terminal_set.append(terminal)

    def addEphemeralConstant(self, ephemeral):
        self.terminal_set.append(ephemeral)
         
    def generate(self, min, max):
        termset_ratio = len(self.terminal_set) / \
                        (len(self.terminal_set)+len(self.primitive_set))
        def generate_expr(max_depth):
            if max_depth == 0 or random.random() < termset_ratio:
                term = random.choice(self.terminal_set)
                if not callable(term):
                    expr = [term]
                else:
                    expr = [term()]
            else:
                func, arity = random.choice(self.primitive_set)
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

    def lambdify(self, expr, args):
        if isinstance(expr, list):
            expr = evaluate(expr)

        if isinstance(args, str):
            pass
        elif hasattr(args, "__iter__"):
            args = ",".join(str(a) for a in args)
        else:
            args = str(args)
        lstr = "lambda %s: (%s)" % (args, expr)
        return eval(lstr, self.func_dict)

