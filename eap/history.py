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

"""The :mod:`~eap.history` module provides a way to generate the genealogy
tree of the famillies of individuals in an evolution.

.. note::
   The genealogy tree might get very big if your population and/or the number
   of generation is large.
"""

import copy
import inspect

class History(object):
    def __init__(self):
        self.genealogy_index = 0
        self.genealogy_history = dict()
        self.genealogy_tree = dict()
    
    def populate(self, individuals):
        for ind in individuals:
            self.genealogy_index += 1
            ind.history_index = self.genealogy_index
            self.genealogy_history[self.genealogy_index] = copy.deepcopy(ind)
            self.genealogy_tree[self.genealogy_index] = list()
        
    def operate(self, *individuals):
        parent_indices = [ind.history_index for ind in individuals]
        
        for ind in individuals:
            self.genealogy_index += 1
            ind.history_index = self.genealogy_index
            self.genealogy_history[self.genealogy_index] = copy.deepcopy(ind)
            self.genealogy_tree[self.genealogy_index] = parent_indices
    
    def getDecorator(self, *argsname):
        def decFunc(func):
            args_name = inspect.getargspec(func)[0]
            args_pos = [args_name.index(name) for name in argsname]
            def wrapFunc(*args, **kargs):
                result = func(*args, **kargs)
                ind_list = [args[index] for index in args_pos]
                self.operate(*ind_list)
                return result
            return wrapFunc
        return decFunc
            
