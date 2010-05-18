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

from bisect import bisect_right
from copy import deepcopy
from itertools import chain
from operator import attrgetter

class HallOfFame(object):
    """The hall of fame contains the best individual that ever lived in the
    population during the evolution.
    """
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.keys = list()
        self.items = list()
    
    def update(self, population):
        """Update the hall of fame with a *population* by replacing the worst
        individuals in the population by the best individuals in the the
        *population* if those individuals are better than that worst from the
        hall of fame.
        """
        if len(self) < self.maxsize:
            # Items are sorted with the best fitness first
            self.items = deepcopy(sorted(chain(self, population), 
                                         key=attrgetter("fitness"), 
                                         reverse=True)[:self.maxsize])
            # The keys are the fitnesses in reverse order to allow the use
            # of the bisection algorithm 
            self.keys = map(attrgetter("fitness"), reversed(self.items))
        else:
            for ind in population: 
                if ind.fitness > self[-1].fitness:
                    # Delete the worst individual from the front
                    self.remove(-1)
                    # Insert the new individual
                    self.insert(ind)
    
    def insert(self, item):
        """Insert a new individual in the hall of fame using the
        :func:`bisect_right` function. The inserted individual is insert
        on the right side of an equal individual. Inserting a new individual
        in the hall of fame also preserve the hall of order's. This method
        **does not** check for the size of the hall of fame, in a way that
        inserting an new individual in a full hall of fame will not remove
        the worst individual to maintain a constant size.
        """
        item = deepcopy(item)
        i = bisect_right(self.keys, item.fitness)
        self.items.insert(len(self) - i, item)
        self.keys.insert(i, item.fitness)
    
    def remove(self, i):
        del self.keys[len(self) - (i % len(self) + 1)]
        del self.items[-1]
    
    def clear(self):
        """Clear the hall of fame."""
        del self.items[:]
        del self.keys[:]

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]

    def __iter__(self):
        return iter(self.items)

    def __reversed__(self):
        return reversed(self.items)
    
    def __repr__(self):
        return repr(self.items)

        
class ParetoFront(list):
    pass        