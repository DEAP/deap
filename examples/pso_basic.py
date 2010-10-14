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

import operator
import random

from math import sin

from eap import base
from eap import creator
from eap import toolbox

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Particle", list, fitness=creator.FitnessMax, speed=list, smin=None, smax=None, best=None)

def generate(size, pmin, pmax, smin, smax):
    part = creator.Particle(random.uniform(pmin, pmax) for _ in xrange(size)) 
    part.speed = [random.uniform(smin, smax) for _ in xrange(size)]
    part.smin = smin
    part.smax = smax
    return part

def updateParticle(part, best, phi1, phi2):
    u1 = (random.uniform(0, phi1),) * len(part)
    u2 = (random.uniform(0, phi2),) * len(part)
    v_u1 = map(operator.mul, u1, map(operator.sub, part.best, part))
    v_u2 = map(operator.mul, u2, map(operator.sub, best, part))
    part.speed = map(operator.add, part.speed, map(operator.add, v_u1, v_u2))
    for i, speed in enumerate(part.speed):
        if speed < part.smin:
            part.speed[i] = part.smin
        elif speed > part.smax:
            part.speed[i] = part.smax
    part[:] = map(operator.add, part, part.speed)
 
def evalH1(x):
    """ Simple two-dimensional function containing several local maxima,
    H1 has a unique maximum value of 2.0 at the point (8.6998, 6.7665).
    From : The Merits of a Parallel Genetic Algorithm in Solving Hard 
    Optimization Problems, A. J. Knoek van Soest and L. J. R. Richard 
    Casius, J. Biomech. Eng. 125, 141 (2003)
    """
    num = (sin(x[0] - x[1] / 8))**2 + (sin(x[1] + x[0] / 8))**2
    denum = ((x[0] - 8.6998)**2 + (x[1] - 6.7665)**2)**0.5 + 1
    return num / denum,

tools = toolbox.Toolbox()
tools.register("particle", generate, size=2, pmin=-100, pmax=100, smin=-50, smax=50)
tools.register("population", list, content_init=tools.particle, size_init=200)
tools.register("update", updateParticle, phi1=2.0, phi2=2.0)
tools.register("evaluate", evalH1)

def main():
    pop = tools.population()
    GEN = 1000
    best = None

    for g in xrange(GEN):
        for part in pop:
            part.fitness.values = tools.evaluate(part)
            if not part.best or part.best.fitness < part.fitness:
                part.best = tools.clone(part)
            if not best or best.fitness < part.fitness:
                best = tools.clone(part) 
        for part in pop:
            tools.update(part, best)

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
    
        length = len(pop)
        mean = sum(fits) / length
        std_dev = abs(sum(x*x for x in fits) / length - mean**2)**0.5

        print "-- Generation %i --" % g
        print "  Min %s" % min(fits)
        print "  Max %s" % max(fits)
        print "  Avg %s" % mean
        print "  Std %s" % std_dev
        print "  Best so far : %s - %s" % (best, best.fitness)

if __name__ == "__main__":
    main()

