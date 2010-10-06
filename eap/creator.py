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

# Warning are turned into errors to catch the DeprecationWarning in the method
# init_type of create.
import warnings
warnings.filterwarnings("error", "", DeprecationWarning, "eap.creator")

def create(name, base, **kargs):
    """The function :func:`create` does create a new class named *name*
    inheriting from *base* in the :mod:`~eap.creator` module. The new
    class can have attributes defined by the subsequent keyworded
    arguments passed to the function create. If the argument is callable,
    it is automatically called in the initialisation of an instance of
    this class and the returned object is added as an attribute of the
    class' instance. Otherwise, if the argument is not callable, (for
    example an :class:`int`), it is added as a "static" attribute of the
    class.
    """
    dict_inst = {}
    dict_cls = {}
    for obj_name, obj in kargs.items():
        if hasattr(obj, "__call__"):
            dict_inst[obj_name] = obj
        else:
            dict_cls[obj_name] = obj

    def initType(self, *args, **kargs):
        """Replace the __init__ function of the new type, in order to
        add attributes, that were defined with **kargs, to the instance.
        """
        for elem in dict_inst.items():
            obj_name, obj = elem
            if hasattr(obj, "__call__"):
                obj = obj()
            setattr(self, obj_name, obj)
        
        # A DeprecationWarning is raised when the object inherits from the 
        # class "object" which leave the option of passing arguments, but
        # raise a warning stating that it will eventually stop permitting
        # this option. Usually this appens when the base class does not
        # override the __init__ method from object.
        try:
            base.__init__(self, *args, **kargs)
        except DeprecationWarning:
            base.__init__(self)

    objtype = type(name, (base,), dict_cls)

    if issubclass(base, array.array):
        def deepcopyArray(self, memo):
            """Overrides the deepcopy from array.array that does not copy
            the object's attributes.
            """
            cls = self.__class__
            copy_ = cls.__new__(cls, self.typecode, self)
            memo[id(self)] = copy_
            copy_.__dict__.update(copy.deepcopy(self.__dict__, memo))
            return copy_
    
        objtype.__deepcopy__ = deepcopyArray

    objtype.__init__ = initType
    globals()[name] = objtype

