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

class IndividualArray(array.array):
    def __new__(cls, typecode, *args, **kargs):
        return super(IndividualArray, cls).__new__(cls, typecode)

    def __init__(self, typecode, size=0, generator=None, fitness=None):
        if fitness is not None:
            try:  # For convenience, the user may pass a fitness object
                self.mFitness = fitness()
            except TypeError:
                self.mFitness = fitness

        for i in xrange(size):
            self.append(generator.next())

    def __copy__(self):
        lCopy = self.__class__.__new__(self.__class__, self.typecode)
        lCopy[:] = self[:]
        lCopy.mFitness = copy.copy(self.mFitness)
        return lCopy

    def __repr__(self):
        return str(list(self)) + ': ' + str(self.mFitness)

    def __reduce__(self):
        return (self.__class__, (self.typecode,), self.__dict__, iter(self))
