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
import eap.base

class BooleanIndividual(eap.base.Individual, array.array):
    def __new__(cls, *args, **kargs):
        return super(BooleanIndividual, cls).__new__(cls, 'b')

    def __init__(self, size, generator, fitness=None):
        eap.base.Individual.__init__(self, fitness)
        for i in xrange(size):
            self.append(generator.next())

    def __copy__(self):
        lCopy = self.__class__.__new__(self.__class__)
        lCopy[:] = self[:]
        lCopy.mFitness = copy.copy(self.mFitness)
        return lCopy

    def __repr__(self):
        return str(list(self)) + ': ' + str(self.mFitness)


class IntegerIndividual(eap.base.Individual, array.array):
    def __new__(cls, *args, **kargs):
        return super(IntegerIndividual, cls).__new__(cls, 'l')

    def __init__(self, size, generator, fitness=None):
        eap.base.Individual.__init__(self, fitness)
        for i in xrange(size):
            self.append(generator.next())

    def __copy__(self):
        lCopy = self.__class__.__new__(self.__class__)
        lCopy[:] = self[:]
        lCopy.mFitness = copy.copy(self.mFitness)
        return lCopy

    def __repr__(self):
        return str(list(self)) + ': ' + str(self.mFitness)


class FloatIndividual(eap.base.Individual, array.array):
    def __new__(cls, *args, **kargs):
        return super(FloatIndividual, cls).__new__(cls, 'd')

    def __init__(self, size, generator, fitness=None):
        eap.base.Individual.__init__(self, fitness)
        for i in xrange(size):
            self.append(generator.next())

    def __copy__(self):
        lCopy = self.__class__.__new__(self.__class__)
        lCopy[:] = self[:]
        lCopy.mFitness = copy.copy(self.mFitness)
        return lCopy

    def __repr__(self):
        return str(list(self)) + ': ' + str(self.mFitness)