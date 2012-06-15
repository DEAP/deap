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
Distributed computation of the prime numbers below 45,000 using DTM.
"""

import time
import math

from deap import dtm

def primaryTest(nbr):
    if nbr <= 2:
        return True
    
    for i in range(2, int(math.sqrt(nbr))+1):
        if nbr % i == 0:
            return False
    return True

def main(upTo):
    beginTime = time.time()
    listNbr = range(3,upTo,2)
    print("Computation begin...")
    listPrimes = dtm.filter(primaryTest, listNbr)
    
    print("Found " + str(len(listPrimes)) + " prime numbers between 3 and " + str(upTo))
    print("Computation time : " + str(time.time()-beginTime))

dtm.start(main, 45003)
