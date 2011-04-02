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

"""The :mod:`~eap.creator` module is the heart and soul of EAP, it allows to
create, at runtime, classes that will fulfill the needs of your evolutionary
algorithms.
"""

import array
import copy
import types

try:
    import numpy
    NUMPY_PRESENT = True
except ImportError:
    NUMPY_PRESENT = False
    
def _deepcopyArray(self, memo):
    """Overrides the deepcopy from array.array that does not copy
    the object's attributes and class type.
    """
    cls = self.__class__
    copy_ = cls.__new__(cls, self.typecode, self)
    memo[id(self)] = copy_
    copy_.__dict__.update(copy.deepcopy(self.__dict__, memo))
    return copy_

def _deepcopyNumPyArray(self, memo):
    """Overrides the deepcopy from numpy.ndarray that does not copy
    the object's attributes.
    """
    copy_ = numpy.ndarray.__deepcopy__(self, memo)
    copy_.__dict__.update(copy.deepcopy(self.__dict__, memo))
    return copy_

@staticmethod
def _newNumPyArray(cls, iterable):
    """Creates a new instance of a numpy.ndarray from a function call"""
    return numpy.array(list(iterable)).view(cls)

def _finalizeNumPyArray(self, obj):
    # __init__ will reinitialize every member of the subclass.
    # this might not be desirable for example in the case of an ES. 
    self.__init__()
    
    # Instead, e could use the following that will simply deepcopy every 
    # member that is present in the original class
    # This is significantly slower. 
    #if self.__class__ == obj.__class__:
    #    self.__dict__.update(copy.deepcopy(obj.__dict__))
    
def create(name, base, **kargs):
    """The function :func:`create` does create a new class named *name*
    inheriting from *base* in the :mod:`~eap.creator` module. The new
    class can have attributes defined by the subsequent keyword
    arguments passed to the function create. If the argument is a class,
    the __init__ function is called in the initialization of an instance of
    the new object and the returned instance is added as an attribute of the
    class' instance. Otherwise, if the argument is not a class, (for
    example an :class:`int`), it is added as a "static" attribute of the
    class.
    """
    dict_inst = {}
    dict_cls = {}
    for obj_name, obj in kargs.iteritems():
        if hasattr(obj, "__call__"):
            dict_inst[obj_name] = obj
        else:
            dict_cls[obj_name] = obj

    # A DeprecationWarning is raised when the object inherits from the 
    # class "object" which leave the option of passing arguments, but
    # raise a warning stating that it will eventually stop permitting
    # this option. Usually this happens when the base class does not
    # override the __init__ method from object.
    def initType(self, *args, **kargs):
        """Replace the __init__ function of the new type, in order to
        add attributes that were defined with **kargs to the instance.
        """
        for obj_name, obj in dict_inst.iteritems():
            setattr(self, obj_name, obj())
        if base.__init__ is not object.__init__:
            base.__init__(self, *args, **kargs)
        else:
            base.__init__(self)

    objtype = type(name, (base,), dict_cls)

    if issubclass(base, array.array):
        objtype.__deepcopy__ = _deepcopyArray
    elif NUMPY_PRESENT and issubclass(base, numpy.ndarray):
        objtype.__deepcopy__ = _deepcopyNumPyArray
        objtype.__new__ = _newNumPyArray
        objtype.__array_finalize__ = _finalizeNumPyArray

    objtype.__init__ = initType
    globals()[name] = objtype

