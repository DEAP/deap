#
#    Copyright 2010, Francois-Michel De Rainville and Felix-Antoine Fortin.
#    
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

import array
import copy
import inspect

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
            if inspect.isclass(obj):
                obj = obj()
            setattr(self, obj_name, obj)
        base.__init__(self, *args)
        
    def repr_type(self):
        out = super(self.__class__, self).__repr__()
        if self.__dict__:
            out = " : ".join([out, repr(self.__dict__)])
        return out
    
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
            #copy_.extend(self)
            return copy_
        
        setattr(objtype, "__deepcopy__", deepcopy_array)
    
    setattr(objtype, "__init__", init_type)
    #if not hasattr(objtype, "__repr__"):
    setattr(objtype, "__repr__", repr_type)
    globals()[name] = objtype

