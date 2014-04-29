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
    from . import hvi as hv
except ImportError:
    # fallback on python version
    from . import pyhv as hv

def hypervolume(front, ref=None):
    """Returns the index of the individual with the least the hypervolume
    contribution.
    """
    
    # Must use wvalues * -1 since hypervolume use implicit minimization
    wobj = numpy.array([ind.fitness.wvalues for ind in front]) * -1
    if ref is None:
        ref = numpy.max(wobj, axis=0) + 1
    
    def contribution(i):
        return hv.hypervolume(numpy.concatenate((wobj[:i], wobj[i+1:])), ref)

    # TODO: Parallelize this?
    contrib_value = map(contribution, range(len(front)))
    return numpy.argmax(contrib_value)

__all__ = ["hypervolume"]