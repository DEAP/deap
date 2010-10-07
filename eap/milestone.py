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

"""The :mod:`milestone` provides a way to save the state of some specified
objects all the way through the evolution.
"""

#import gzip
import random
try:
    import yaml
    USE_YAML = True
    try:
        from yaml import CDumper as Dumper  # CLoader and CDumper are much
        from yaml import CLoader as Loader  # faster than default ones, but 
    except ImportError:                     # requires LibYAML to be compiled
        from yaml import Dumper
        from yaml import Loader
except ImportError:
    USE_YAML = False
                                            # If yaml ain't present, use 
try:                                        # pickling to dump
    import cPickle as pickle                # cPickle is much faster than 
except ImportError:                         # pickle but only present under
    import pickle                           # CPython

class Milestone(object):
    """A milestone is a file containing the state of any object that has been
    hooked. While initializing a milestone, add the objects that you want to
    be dumped by appending keyworded arguments to the initializer or using the 
    :meth:`add`. By default the milestone tries to use the YAML format wich
    is human readable, if PyYAML is not installed, it uses pickling wich is
    not readable. You can force the use of pickling by setting the argument
    *yaml* to :data:`False`. 
    
    In order to use efficiently this module, you must understand properly the
    assignement principles in Python. This module use the *pointers* you passed
    to dump the object, for example the following won't work as desired ::
    
        >>> my_object = [1, 2, 3]
        >>> ms = Milestone(obj=my_object)
        >>> my_object = [3, 5, 6]
        >>> ms.dump("example")
        >>> ms.load("example.ems")
        >>> ms["obj"]
        [1, 2, 3]
        
    In order to dump the new value of ``my_object`` it is needed to change its
    internal values directly and not touch the *label*, as in the following ::
    
        >>> my_object = [1, 2, 3]
        >>> ms = Milestone(obj=my_object)
        >>> my_object[:] = [3, 5, 6]
        >>> ms.dump("example")
        >>> ms.load("example.ems")
        >>> ms["obj"]
        [3, 5, 6]
        
    """
    def __init__(self, yaml=True, **kargs):
#        self.zipped = zipped
        self._dict = kargs
        if USE_YAML and yaml:
            self.use_yaml = True
        else:
            self.use_yaml = False
    
    def add(self, **kargs):
        """Add objects to the list of objects to be dumped. The object is added
        under the name specified by the argument's name. Keyworded arguments
        are mandatory in this function."""
        self._dict.update(*kargs)
    
    def remove(self, *args):
        """Remove objects with the specified name from the list of objects to
        be dumped.
        """
        for element in args:
            del self._dict[element]
    
    def __getitem__(self, value):
        return self._dict[value]
    
    def dump(self, prefix):
        """Dump the current registered objects in a file named *prefix.ems*,
        the randomizer state is always added to the file and available under
        the ``"randomizer_state"`` tag.
        """
#        if not self.zipped:
        ms_file = open(prefix + ".ems", "w")
#        else:
#            file = gzip.open(prefix + ".ems.gz", "w")
        ms = self._dict.copy()
        ms.update({"randomizer_state" : random.getstate()})
        
        if self.use_yaml:
            ms_file.write(yaml.dump(ms, Dumper=Dumper))
        else:
            pickle.dump(ms, ms_file)
        
        ms_file.close()
    
    def load(self, filename):
        """Load a milestone file retreiving the dumped objects, it is not safe
        to load a milestone file in a milestone object that contians
        references as all conflicting names will be updated with the new
        values.
        """
        if self.use_yaml:
            self._dict.update(yaml.load(open(filename, "r"), Loader=Loader))
        else:
            self._dict.update(pickle.load(open(filename, "r")))
        
