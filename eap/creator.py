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

"""The :mod:`creator` module allows to create and contain types (classes)
built at runtime. Its only function :func:`~eap.creator.create` creates types
and store them into the globals of this module. The main purpose of the creator
is to allow the user to create its very own kind of structures from the base
types defined in the :mod:`~eap.base` module. A secondary
purpose is that when storing the new types with the same name they have been
created with, pickling is made possible. 
"""

import inspect

def create(name, bases, dict={}):
    """Instanciates new class and store it under :class:`eap.creator`\ .\ *name*\ . The
    *base* argument is a tuple of base classes (see the :func:`type` built-in
    function).
    
    The optional *dict* argument may contain callable or non-callable objects.
    If the object is callable, then it will be automatically called when an
    object of this type is initialized, adding the return value of the call to
    an attribute named by the name assigned in the dictionary. If it is not
    callable, it will be passed to the underlying :func:`type` function.
    """
    dict_inst = {}
    dict_cls = {}
    for obj_name, obj in dict.items():
        #if inspect.isclass(obj):
        if callable(obj):
            dict_inst[obj_name] = obj
        else:
            dict_cls[obj_name] = obj

    def init_type(self, *args, **kargs):
        for obj_name, obj in dict_inst.items():
            setattr(self, obj_name, obj())

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

