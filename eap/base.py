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

"""The :mod:`~eap.base` module provides basic structures to build evolutionary
algorithms.
"""

import array
import copy
import operator
import random

from collections import deque
from itertools import izip, repeat, count, chain, imap
import itertools
        
class Tree(list):
    """ Basic N-ary tree class"""
    class Node(object):
        height = 0
        size = 1
        @property
        def root(self):
            return self
        def __getstate__(self):
            try:
                return self.base(self)
            except TypeError:
                base = self.base.__new__(self.base)
                base.__dict__.update(self.__dict__)
                return base

    @classmethod
    def create_node(cls, obj):
        Node = type("Node", (type(obj),cls.Node), {})
        Node.base = type(obj)
        try:
            new_node = Node.__new__(Node)
            new_node.__dict__.update(obj.__dict__)
        except AttributeError:
            new_node = Node(obj)
            
        return new_node

    @classmethod
    def rectify_subtree(cls, subtree):
        if subtree.size > 1:
            return subtree
        else:
            return subtree.root

    def __init__(self, content=None):
        if hasattr(content, "__call__"):
            content = content()
        for elem in content:
            if isinstance(elem, list):
                self.append(Tree(elem))
            else:
                self.append(Tree.create_node(elem))
    
    def __getstate__(self):
        """ This methods returns the state of the Tree
            as a list of arbitrary elements. It is mainly
            used for pickling a Tree object.
        """
        return [elem.__getstate__() for elem in self]
        
#    def __setstate__(self, state):
#        self.__init__(state)
    
    def __reduce__(self):
        return (self.__class__, (self.__getstate__(),), self.__dict__)
    
    @property
    def root(self):
        """Returns the root element of the tree."""
        return self[0]

    @property
    def size(self):
        """ This method returns the number of nodes in the tree."""
        return sum(elem.size for elem in self)

    @property
    def height(self):
        """ This method returns the height of the tree."""
        return max(elem.height for elem in self)+1

    def search_subtree_dfs(self, index):
        """ This method searches the subtree with the
            corresponding index based on a depth first
            search.
        """
        if index == 0:
            return self
        total = 0
        for child in self:
            if total == index:
                return child
            nbr_child = child.size
            if nbr_child + total > index:
                return child.search_subtree_dfs(index-total)
            total += nbr_child

    def set_subtree_dfs(self, index, subtree):
        """ This method replaced the tree with
            the corresponding index by subtree based
            on a depth-first search.
        """
        if index == 0:
            self[:] = subtree
            return
        total = 0
        for i, child in enumerate(self):
            if total == index:
                self[i] = Tree.rectify_subtree(subtree)
                return
            nbr_child = child.size
            if nbr_child + total > index:
                child.set_subtree_dfs(index-total, subtree)
                return
            total += nbr_child

    def search_subtree_bfs(self, index):
        """ This method searches the subtree with the
            corresponding index based on a breadth-first
            search.
        """
        if index == 0:
            return self
        queue = deque(self[1:])
        total = 0
        while total != index:
            total += 1
            subtree = queue.popleft()
            if isinstance(subtree, Tree):
                queue.extend(subtree[1:])
        return subtree

    def set_subtree_bfs(self, index, subtree):
        """ This method replaced the subtree with
            the corresponding index by subtree based
            on a breadth-first search.
        """
        if index == 0:
            self[:] = subtree
            return
        queue = deque(izip(repeat(self, len(self[1:])), count(1)))
        total = 0
        while total != index:
            total += 1
            elem = queue.popleft()
            parent = elem[0]
            child  = elem[1]
            if isinstance(parent[child], Tree):
                tree = parent[child]
                queue.extend(izip(repeat(tree, len(tree[1:])), count(1)))
        parent[child] = Tree.rectify_subtree(subtree)

class Fitness(object):
    """The fitness is a measure of quality of a solution. The fitness
    inheritates from the :class:`Array` class, so the number of objectives
    depends on the lenght of the array.

    Fitnesses may be compared using the ``>``, ``<``, ``>=``, ``<=``, ``==``,
    ``!=`` and :meth:`cmp` operators. The comparison of those operators is made
    lexicographically. Maximization and minimization are taken
    care off by a multiplication between the :attr:`weights` and the fitness values.
    The comparison can be made between fitnesses of different size, if the
    fitnesses are equal until the extra elements, the longer fitness will be
    superior to the shorter.

    .. note::
       When comparing fitness values that are minimized, ``a > b`` will return
       :data:`True` if *a* is inferior to *b*.
    """
    
    weights = ()
    """The weights are used in the fitness comparison. They are shared among
    all fitnesses of the same type.
    This member is **not** meant to be manipulated since it may influence how
    fitnesses are compared and may
    result in undesirable effects. However if you wish to manipulate it, in 
    order to make the change effective to all fitnesses of the same type, use
    ``FitnessType.weights = new_weights`` or
    ``self.__class__.weights = new_weights`` or from an individual
    ``ind.fitness.__class__.weights = new_weights``.
    """
    
    def __init__(self, values=None):
        self._values = values
    
    def getvalid(self):
        return self._values is not None
    
    def setvalid(self, values):
        if not values:
            self._values = None
        
    valid = property(getvalid, setvalid, None, 
                     "Asses if a fitness is valid or not.")
    
    def getvalues(self):
        return self._values
    
    def setvalues(self, values):
        if values is None:
            self._values = None
        else:
            try:
                self._values = tuple(values)
            except TypeError:
                self._values = tuple((values,))
    
    values = property(getvalues, setvalues, None,
                      "Set the fitness to a single value or a tupe of values.")

    def isDominated(self, other):
        '''In addition to the comparaison operators that are used to sort
        lexically the fitnesses, this method returns :data:`True` if this
        fitness is dominated by the *other* fitness and :data:`False` otherwise.
        The weights are used to compare minimizing and maximizing fitnesses. If
        there is more fitness values than weights, the las weight get repeated
        until the end of the comparaison.
        '''
        not_equal = False
        # Pad the weights with the last value
#        weights = itertools.chain(self.weights, repeat(self.weights[-1]))
        for weight, self_value, other_value in izip(self.weights, self, other):
            self_w_value = self_value * weight
            other_w_value = other_value * weight
            if self_w_value > other_w_value:
                return False
            elif self_w_value < other_w_value:
                not_equal = True
        return not_equal

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __lt__(self, other):
        if other in (None, tuple()):    # Protection against yamling
            return False
        # Pad the weights with the last value
        #weights = chain(self.weights, repeat(self.weights[-1]))
        # Apply the weights to the values
        self_values = map(operator.mul, self.values, self.weights)
        other_values = map(operator.mul, other.values, other.weights)
        # Compare the results
        #print "%r < %r = %s" % (self_values, other_values, self_values < other_values)
        return self_values < other_values

    def __le__(self, other):
        if other in (None, tuple()):    # Protection against yamling
            return False
        # Pad the weights with the last value
        #weights = chain(self.weights, repeat(self.weights[-1]))
        # Apply the weights to the values
        self_values = map(operator.mul, self.values, self.weights)
        other_values = map(operator.mul, other.values, other.weights)
        # Compare the results
        return self_values <= other_values

    def __eq__(self, other):
        if other in (None, tuple()):    # Protection against yamling
            return False
        # Pad the weights with the last value
        #weights = chain(self.weights, repeat(self.weights[-1]))
        # Apply the weights to the values
        self_values = map(operator.mul, self.values, self.weights)
        other_values = map(operator.mul, other.values, other.weights)
        # Compare the results
        return self_values == other_values

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if self > other:
            return 1
        elif other > self:
            return -1
        return 0
    
    def __deepcopy__(self, memo):
        cls = self.__class__
        copy_ = cls.__new__(cls)
        cls.__init__(copy_, None)
        if self.values is not None:
            # Warning : when copying the fitness, elements shall be immutable
            copy_.values = tuple(self.values)
        else:
            copy_.values = None
        memo[id(self)] = copy_
        # Add a memo to tell not to copy the values again when updating the dict
        memo[id(self.values)] = copy_.values
        copy_.__dict__.update(copy.deepcopy(self.__dict__, memo))
        return copy_
    
    #def __repr__(self):
    #    return repr(self.values)
        