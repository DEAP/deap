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
    from . import hv as hv
except ImportError:
    # fallback on python version
    from . import pyhv as hv

def hypervolume(front, ref=None):
    """Returns the index of the individual with the least the hypervolume
    contribution.
    """
    # Must use wvalues * -1 since hypervolume use implicit minimization
    # And minimization in deap use max on -obj
    wobj = numpy.array([ind.fitness.wvalues for ind in front]) * -1
    if ref is None:
        ref = numpy.max(wobj, axis=0) + 1

    # Ensure the extreme points get highest rank
    # Don't compute the hypervolume for them
    max_obj = set(numpy.argmin(wobj, axis=0))
    indices = [x for x in range(len(front)) if x not in max_obj]
    # indices = range(len(front))
    
    def contribution(i):
        return hv.hypervolume(numpy.concatenate((wobj[:i], wobj[i+1:])), ref)

    # TODO: Parallelize this?
    contrib_values = map(contribution, indices)
    
    # Reinsert the extreme points with minimal value
    for i in sorted(max_obj):
        contrib_values.insert(i, 0)

    # Select the maximum hypervolume value
    return numpy.argmax(contrib_values)

__all__ = ["hypervolume"]