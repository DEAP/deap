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

import inspect

def create(name, bases, dict={}):
    dict_inst = {}
    dict_cls = {}
    for obj_name, obj in dict.items():
        if inspect.isclass(object):
            dict_inst[obj_name] = obj
        else:
            dict_cls[obj_name] = obj

    def init_type(self, **kargs):
        for elem in dict_inst.items():
            obj_name, object = elem
            if inspect.isclass(object):
                object = object()
            setattr(self, obj_name, object)

        for base in bases:
            base_args = {}
            args_spec = inspect.getargspec(base.__init__)
            for arg in args_spec[0][1:]:
                if kargs.has_key(arg):
                    base_args[arg] = kargs[arg]
            base.__init__(self, **base_args)
            

    objtype = type(name, bases, dict_cls)
    setattr(objtype, "__init__", init_type)
    globals()[name] = objtype

