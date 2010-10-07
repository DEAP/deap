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

try:
    from itertools import permutations
except ImportError:
    def permutations(iterable, r=None):
        """Permutation function as defined in the itertools module. It is used
        if the permutation function in itertools ain't present (python 2.5 and
        lower).
        """
        # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
        # permutations(range(3)) --> 012 021 102 120 201 210
        pool = tuple(iterable)
        n = len(pool)
        r = n if r is None else r
        if r > n:
            return
        indices = range(n)
        cycles = range(n, n-r, -1)
        yield tuple(pool[i] for i in indices[:r])
        while n:
            for i in reversed(range(r)):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i+1:] + indices[i:i+1]
                    cycles[i] = n - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    yield tuple(pool[i] for i in indices[:r])
                    break
            else:
                return

class SortingNetwork(list):
    """Sorting network class.
    
    From Wikipedia : A sorting network is an abstract mathematical model
    of a network of wires and comparator modules that is used to sort a
    sequence of numbers. Each comparator connects two wires and sort the
    values by outputting the smaller value to one wire, and a larger
    value to the other.
    """
    def __init__(self, dimension, connectors = []):
        self.dimension = dimension
        for wire1, wire2 in connectors:
            self.addConnector(wire1, wire2)
    
    def addConnector(self, wire1, wire2):
        """Add a connector between wire1 and wire2 in the network."""
        if wire1 == wire2:
            return
        
        if wire1 > wire2:
            wire1, wire2 = wire2, wire1
        
        try:
            last_level = self[-1]
        except IndexError:
            # Empty network, create new level and connector
            self.append({wire1: wire2})
            return
        
        for wires in last_level.items():
            if wires[1] >= wire1 and wires[0] <= wire2:
                self.append({wire1: wire2})
                return
        
        last_level[wire1] = wire2
    
    def sort(self, values):
        """Sort the values in-place based on the connectors in the network."""
        for level in self:
            for wire1, wire2 in level.items():
                if values[wire1] > values[wire2]:
                    values[wire1], values[wire2] = values[wire2], values[wire1]
    
    def assess(self):
        """Test all possible inputs given the dimension of the network,
        and return the number of incorrectly sorted inputs.
        """
        ordered = range(self.dimension)
        misses = 0
        for sequence in permutations(ordered):
            sequence = list(sequence)
            self.sort(sequence)
            if ordered != sequence:
                misses += 1
        return misses
    
    def draw(self):
        """Return an ASCII representation of the network."""
        str_wires = [["-"]*7 * self.depth]
        str_wires[0][0] = "0"
        str_wires[0][1] = " o"
        str_spaces = []

        for i in xrange(1, self.dimension):
            str_wires.append(["-"]*7 * self.depth)
            str_spaces.append([" "]*7 * self.depth)
            str_wires[i][0] = str(i)
            str_wires[i][1] = " o"
        
        for index, level in enumerate(self):
            for wire1, wire2 in level.items():
                str_wires[wire1][(index+1)*6] = "x"
                str_wires[wire2][(index+1)*6] = "x"
                for i in xrange(wire1, wire2):
                    str_spaces[i][(index+1)*6+1] = "|"
                for i in xrange(wire1+1, wire2):
                    str_wires[i][(index+1)*6] = "|"
        
        network_draw = "".join(str_wires[0])
        for line, space in zip(str_wires[1:], str_spaces):
            network_draw += "\n"
            network_draw += "".join(space)
            network_draw += "\n"
            network_draw += "".join(line)
        return network_draw
    
    @property
    def depth(self):
        """Return the number of parallel steps that it takes to sort any input.
        """
        return len(self)
    
    @property
    def length(self):
        """Return the number of comparison-swap used."""
        return sum(len(level) for level in self)

