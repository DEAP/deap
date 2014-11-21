#    Copyright (C) 2010 Simon Wessing
#    TU Dortmund University
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy

try:
    # try importing the C version
    from ._hypervolume import hv as hv
except ImportError:
    # fallback on python version
    from ._hypervolume import pyhv as hv

def hypervolume(front, **kargs):
    """Returns the index of the individual with the least the hypervolume
    contribution. The provided *front* should be a set of non-dominated
    individuals having each a :attr:`fitness` attribute. 
    """
    # Must use wvalues * -1 since hypervolume use implicit minimization
    # And minimization in deap use max on -obj
    wobj = numpy.array([ind.fitness.wvalues for ind in front]) * -1
    ref = kargs.get("ref", None)
    if ref is None:
        ref = numpy.max(wobj, axis=0) + 1
    
    def contribution(i):
        # The contribution of point p_i in point set P
        # is the hypervolume of P without p_i
        return hv.hypervolume(numpy.concatenate((wobj[:i], wobj[i+1:])), ref)

    # Parallelization note: Cannot pickle local function
    contrib_values = map(contribution, range(len(front)))

    # Select the maximum hypervolume value (correspond to the minimum difference)
    return numpy.argmax(contrib_values)

def additive_epsilon(front, **kargs):
    """Returns the index of the individual with the least the additive epsilon
    contribution. The provided *front* should be a set of non-dominated
    individuals having each a :attr:`fitness` attribute.

    .. warning::

       This function has not been tested.
    """
    wobj = numpy.array([ind.fitness.wvalues for ind in front]) * -1

    def contribution(i):
        mwobj = numpy.ma.array(wobj)
        mwobj[i] = numpy.ma.masked
        return numpy.min(numpy.max(wobj[i] - mwobj, axis=1))
        
    contrib_values = map(contribution, range(len(front)))

    # Select the minimum contribution value
    return numpy.argmin(contrib_values)


def multiplicative_epsilon(front, **kargs):
    """Returns the index of the individual with the least the multiplicative epsilon
    contribution. The provided *front* should be a set of non-dominated
    individuals having each a :attr:`fitness` attribute.

    .. warning::

       This function has not been tested.
    """
    wobj = numpy.array([ind.fitness.wvalues for ind in front]) * -1

    def contribution(i):
        mwobj = numpy.ma.array(wobj)
        mwobj[i] = numpy.ma.masked
        return numpy.min(numpy.max(wobj[i] / mwobj, axis=1))
        
    contrib_values = map(contribution, range(len(front)))

    # Select the minimum contribution value
    return numpy.argmin(contrib_values)



__all__ = ["hypervolume", "additive_epsilon", "multiplicative_epsilon"]