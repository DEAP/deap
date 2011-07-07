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

"""
A very simple example of recursive nested tasks.
Each task maps 2 others tasks, each of these 2 tasks maps 2 others, etc.,
up to RECURSIVITY_LEVEL.

Setting RECURSIVITY_LEVEL to a high value (typically more than 16) may
produce some strange OS errors (as the kernel will probably complain about
the number of active threads...
"""

from deap import dtm

RECURSIVITY_LEVEL = 12

def recursiveFunc(level):
    if level == 1:
        return 1
    else:
        args = [level-1] * 2
        s = sum(dtm.map(recursiveFunc, args))
        if level == RECURSIVITY_LEVEL:
            print("2^"+str(level)+" = " + str(s))
        return s

dtm.start(recursiveFunc, RECURSIVITY_LEVEL)
