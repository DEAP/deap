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

"""The :class:`~eap.toolbox.Toolbox` is intended to contain the operators that
you need in your evolutionary algorithms, from initialization to evaluation.
It is always possible to use directly the operators from this module, but the
toolbox is also intended to contain the default values of the different
parameters for each method. Moreover, it makes your algorithms easier to
understand and modify, since once an operator is set, it can be reused with a
simple keyword that contains all its arguments. For example, if a user needs a
hammer in his algorithm, but has access to several hammer designs, he will
choose the one model best suited for his current problem, say 'HammerXYZ', and
register it into the toolbox with a generic 'Hammer' alias. In this way, he
will be able to build algorithms that are decoupled from operator sets. If he
later decides that some other hammer is better suited, his algorithm will
remain unchanged, he will only need to update the toolbox used by the
algorithm. In that same way, the toolbox is integrand part of the predefined
algorithms from the :mod:`~eap.algorithms` module.
"""

import copy
import functools
import inspect
from itertools import cycle

class Repeat(object):
    """Functional object that repeat a function *func*
    a number of times *times*, then raise a StopIteration
    exception. It implements the Python iterator model.

    This class allows to fill a list with objects produced
    by a function.
    """
    def __init__(self, func, times):
        self.func = func
        self.count = cycle(xrange(times+1))
        self.times = times
        
    def __iter__(self):
        return self
        
    def next(self):
        """Function use to iterate."""
        if self.count.next() == self.times:
            raise StopIteration
        return self.func()
    
class Iterate(object):
    """Functional object used to cycle on the iterable object
    returned by a function *func*. The function is
    called when there is no longer any possible 
    iteration that can be done on the object.
    """
    def __init__(self, func):
        self.func = func
        self.iter = None
        
    def __iter__(self):
        return self
        
    def next(self):
        """Function use to iterate."""
        try:
            return self.iter.next()
        except StopIteration:
            self.iter = iter(self.func())
            raise StopIteration
        except AttributeError:
            self.iter = iter(self.func())
            return self.iter.next()

class FuncCycle(object):
    """Functionnal object use to cycle and call a 
    list of functions.
    """
    def __init__(self, seq_func):
        self.cycle = cycle(func for func in seq_func)
    def __call__(self):
        return self.cycle.next()()
        
def fill_repeat(container, func, dim):
    return container(func() for _ in xrange(dim))

def fill_iter(container, generator):
    return container(generator())

# def fill_funccycle(container, seq_func):

class Toolbox(object):
    """A toolbox for evolution that contains the evolutionary operators.
    At first the toolbox contains two simple methods. The first method
    :meth:`~eap.toolbox.clone` duplicates any element it is passed as
    argument, this method defaults to the :func:`copy.deepcopy` function.
    The second method :meth:`~eap.toolbox.map` applies the function given
    as first argument to every items of the iterables given as next
    arguments, this method defaults to the :func:`map` function. You may
    populate the toolbox with any other function by using the
    :meth:`~eap.toolbox.register` method.
    """
    
    def __init__(self):
        self.register("clone", copy.deepcopy)
        self.register("map", map)

    def register(self, methodname, method, *args, **kargs):
        """Register a *method* in the toolbox under the name *methodname*. You 
        may provide default arguments that will be passed automatically when 
        calling the registered method. Fixed arguments can then be overriden 
        at function call time. The following code block is a example of how
        the toolbox is used.
        ::
        
            >>> def func(a, b, c=3):
            ...     print a, b, c
            ... 
            >>> tools = Toolbox()
            >>> tools.register("myFunc", func, 2, c=4)
            >>> tools.myFunc(3)
            2 3 4
        
        """
        pfunc = functools.partial(method, *args, **kargs)
        pfunc.__name__ = methodname
        setattr(self, methodname, pfunc)
    
    def unregister(self, methodname):
        """Unregister *methodname* from the toolbox."""
        delattr(self, methodname)
        
    def decorate(self, methodname, *decorators):
        """Decorate *methodname* with the specified *decorators*, *methodname*
        has to be a registered function in the current toolbox. Decorate uses
        the signature preserving decoration function
        :func:`~eap.toolbox.decorate`.
        """
        partial_func = getattr(self, methodname)
        method = partial_func.func
        args = partial_func.args
        kargs = partial_func.keywords
        for decorator in decorators:
            method = decorate(decorator)(method)
        setattr(self, methodname, functools.partial(method, *args, **kargs))
        


######################################
# Decoration tool                    #
######################################

# This function is a simpler version of the decorator module (version 3.2.0)
# from Michele Simionato available at http://pypi.python.org/pypi/decorator.
# Copyright (c) 2005, Michele Simionato
# All rights reserved.
# Modified by Francois-Michel De Rainville, 2010

def decorate(decorator):
    """Decorate a function preserving its signature. There is two way of
    using this function, first as a decorator passing the decorator to
    use as argument, for example ::
    
        @decorate(a_decorator)
        def myFunc(arg1, arg2, arg3="default"):
            do_some_work()
            return "some_result"
    
    Or as a decorator ::
    
        @decorate
        def myDecorator(func):
            def wrapFunc(*args, **kargs):
                decoration_work()
                return func(*args, **kargs)
            return wrapFunc
        
        @myDecorator
        def myFunc(arg1, arg2, arg3="default"):
            do_some_work()
            return "some_result"
    
    Using the :mod:`inspect` module, we can retrieve the signature of the
    decorated function, what is not possible when not using this method. ::
    
        print inspect.getargspec(myFunc)
        
    It shall return something like ::
    
        (["arg1", "arg2", "arg3"], None, None, ("default",))
    
    This function is a simpler version of the decorator module (version 3.2.0)
    from Michele Simionato available at http://pypi.python.org/pypi/decorator.
    """
    def wrapDecorate(func):
        # From __init__
        assert func.__name__
        if inspect.isfunction(func):
            argspec = inspect.getargspec(func)
            defaults = argspec[-1]
            signature = inspect.formatargspec(formatvalue=lambda val: "",
                                              *argspec)[1:-1]
        elif inspect.isclass(func):
            argspec = inspect.getargspec(func.__init__)
            defaults = argspec[-1]
            signature = inspect.formatargspec(formatvalue=lambda val: "",
                                              *argspec)[1:-1]
        if not signature:
            raise TypeError("You are decorating a non function: %s" % func)
    
        # From create
        src = ("def %(name)s(%(signature)s):\n"
               "    return _call_(%(signature)s)\n") % dict(name=func.__name__,
                                                           signature=signature)
    
        # From make
        evaldict = dict(_call_=decorator(func))
        reserved_names = set([func.__name__] + \
            [arg.strip(' *') for arg in signature.split(',')])
        for name in evaldict.iterkeys():
            if name in reserved_names:
                raise NameError("%s is overridden in\n%s" % (name, src))
        try:
            # This line does all the dirty work of reassigning the signature
            code = compile(src, "<string>", "single")
            exec code in evaldict
        except:
            raise RuntimeError("Error in generated code:\n%s" % src)
        new_func = evaldict[func.__name__]
    
        # From update
        new_func.__source__ = src
        new_func.__name__ = func.__name__
        new_func.__doc__ = func.__doc__
        new_func.__dict__ = func.__dict__.copy()
        new_func.func_defaults = defaults
        new_func.__module__ = func.__module__
        return new_func
    return wrapDecorate
