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

"""The :mod:`history` module provides a way to generate the genealogy
tree of the famillies of individuals in an evolution.

.. note::
   The genealogy tree might get very big if your population and/or the number
   of generation is large.
"""

import copy
import inspect

class History(object):
    """The :class:`History` class helps to build a genealogy of all the
    individuals produced in the evolution. It contains two attributes,
    the :attr:`genealogy_tree` that is a dictionary of lists indexed by
    individual, the list contain the indice of the parents. The second
    attribute :attr:`genealogy_history` contains every individual indexed
    by their individual number as in the genealogy tree.
    
    The produced genealogy tree is compatible with `NetworkX
    <http://networkx.lanl.gov/index.html>`_, here is how to plot the genealogy
    tree ::
    
        hist = History()
        
        # Do some evolution and fill the history
        
        import matplotlib.pyplot as plt
        import networkx as nx
        
        g = nx.DiGraph(hist.genealogy_tree)
        nx.draw_springs(g)
        plt.show()
        
    """
    def __init__(self):
        self.genealogy_index = 0
        self.genealogy_history = dict()
        self.genealogy_tree = dict()
    
    def populate(self, individuals):
        """Populate the history with the initial *individuals*. An attribute
        :attr:`history_index` is added to every individual, this index will 
        help to track the parents and the childs through evolution. This index
        will be modified by the :meth:`update` method when a child is produced.
        Modifying the internal :attr:`genealogy_index` of the history or the
        :attr:`history_index` of an individual may lead to unpredictable
        results and corruption of the history.
        """
        for ind in individuals:
            self.genealogy_index += 1
            ind.history_index = self.genealogy_index
            self.genealogy_history[self.genealogy_index] = copy.deepcopy(ind)
            self.genealogy_tree[self.genealogy_index] = list()
        
    def update(self, *individuals):
        """Update the history with the new *individuals*. The index present
        in their :attr:`history_index` attribute will be used to locate their
        parents and modified to a unique one to keep track of those new
        individuals.
        """
        parent_indices = [ind.history_index for ind in individuals]
        
        for ind in individuals:
            self.genealogy_index += 1
            ind.history_index = self.genealogy_index
            self.genealogy_history[self.genealogy_index] = copy.deepcopy(ind)
            self.genealogy_tree[self.genealogy_index] = parent_indices
    
    def getDecorator(self, *argsname):
        """Function that returns an appropriate decorator to enhance the
        operators of the toolbox. *argsname* is the name of the arguments that
        shall be treated as individuals in the decorated function. The order
        of operations is first the call to the undecorated operator then to
        the update function with as arguments the arguments of the operator
        specified by *argsname*.
        """
        def decFunc(func):
            args_name = inspect.getargspec(func)[0]
            args_pos = [args_name.index(name) for name in argsname]
            def wrapFunc(*args, **kargs):
                result = func(*args, **kargs)
                ind_list = [args[index] for index in args_pos]
                self.update(*ind_list)
                return result
            return wrapFunc
        return decFunc
            
