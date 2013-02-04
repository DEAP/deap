#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.


from itertools import product

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

        index = 0
        for level in reversed(self):
            if self.checkConflict(level, wire1, wire2):
                break
            index -= 1
        
        if index == 0:
            self.append([(wire1, wire2)])
        else:
            self[index].append((wire1, wire2))

    def checkConflict(self, level, wire1, wire2):
        """Check if a connection between `wire1` and `wire2` can be 
        added on this `level`."""
        for wires in level:
            if wires[1] >= wire1 and wires[0] <= wire2:
                return True
    
    def sort(self, values):
        """Sort the values in-place based on the connectors in the network."""
        for level in self:
            for wire1, wire2 in level:
                if values[wire1] > values[wire2]:
                    values[wire1], values[wire2] = values[wire2], values[wire1]
    
    def assess(self, cases=None):
        """Try to sort the **cases** using the network, return the number of
        misses. If **cases** is None, test all possible cases according to
        the network dimensionality.
        """
        if cases is None:
            cases = product((0, 1), repeat=self.dimension)
        
        misses = 0
        ordered = [[0]*(self.dimension-i) + [1]*i for i in range(self.dimension+1)]
        for sequence in cases:
            sequence = list(sequence)
            self.sort(sequence)
            misses += (sequence != ordered[sum(sequence)])
        return misses
    
    def draw(self):
        """Return an ASCII representation of the network."""
        str_wires = [["-"]*7 * self.depth]
        str_wires[0][0] = "0"
        str_wires[0][1] = " o"
        str_spaces = []

        for i in range(1, self.dimension):
            str_wires.append(["-"]*7 * self.depth)
            str_spaces.append([" "]*7 * self.depth)
            str_wires[i][0] = str(i)
            str_wires[i][1] = " o"
        
        for index, level in enumerate(self):
            for wire1, wire2 in level:
                str_wires[wire1][(index+1)*6] = "x"
                str_wires[wire2][(index+1)*6] = "x"
                for i in range(wire1, wire2):
                    str_spaces[i][(index+1)*6+1] = "|"
                for i in range(wire1+1, wire2):
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

