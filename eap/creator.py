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

def create(name, base, **kargs):
    dict_inst = {}
    dict_cls = {}
    for obj_name, obj in kargs.items():
        if callable(obj):
            dict_inst[obj_name] = obj
        else:
            dict_cls[obj_name] = obj

    def init_type(self, *args, **kargs):
        for elem in dict_inst.items():
            obj_name, obj = elem
            if callable(obj):
                obj = obj()
            setattr(self, obj_name, obj)
            
        # A DeprecationWarning is raised when the object inherits from the 
        # class "object" which leave the option of passing arguments, but
        # raise a warning stating that it will eventually stop permitting
        # this option.
        try:
            base.__init__(self, *args, **kargs)
        except (DeprecationWarning):
            base.__init__(self)
    
    objtype = type(name, (base,), dict_cls)
    
    if issubclass(base, array.array):
        def deepcopy_array(self, memo):
            """Overrides the deepcopy from array.array that does not copy the
            object's attributes.
            """
            cls = self.__class__
            copy_ = cls.__new__(cls, self.typecode, self)
            memo[id(self)] = copy_
            copy_.__dict__.update(copy.deepcopy(self.__dict__, memo))
            return copy_
        
        objtype.__deepcopy__ = deepcopy_array
    
    objtype.__init__ = init_type
    globals()[name] = objtype

