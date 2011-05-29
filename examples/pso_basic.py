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

import operator
import random

from deap import base
from deap import benchmarks
from deap import creator
from deap import operators
from deap import toolbox

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Particle", list, fitness=creator.FitnessMax, speed=list, smin=None, smax=None, best=None)

def generate(size, pmin, pmax, smin, smax):
    part = creator.Particle(random.uniform(pmin, pmax) for _ in xrange(size)) 
    part.speed = [random.uniform(smin, smax) for _ in xrange(size)]
    part.smin = smin
    part.smax = smax
    return part

def updateParticle(part, best, phi1, phi2):
    u1 = (random.uniform(0, phi1) for _ in range(len(part)))
    u2 = (random.uniform(0, phi2) for _ in range(len(part)))
    v_u1 = map(operator.mul, u1, map(operator.sub, part.best, part))
    v_u2 = map(operator.mul, u2, map(operator.sub, best, part))
    part.speed = map(operator.add, part.speed, map(operator.add, v_u1, v_u2))
    for i, speed in enumerate(part.speed):
        if speed < part.smin:
            part.speed[i] = part.smin
        elif speed > part.smax:
            part.speed[i] = part.smax
    part[:] = map(operator.add, part, part.speed)

tools = toolbox.Toolbox()
tools.register("particle", generate, size=2, pmin=-100, pmax=100, smin=-50, smax=50)
tools.register("population", list, toolbox.Repeat(tools.particle, 50))
tools.register("update", updateParticle, phi1=2.0, phi2=2.0)
tools.register("evaluate", benchmarks.h1)

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    pop = tools.population()
    stats = tools.clone(stats_t)
    GEN = 1000
    best = None

    for g in xrange(GEN):
        print "-- Generation %i --" % g        
        for part in pop:
            part.fitness.values = tools.evaluate(part)
            if not part.best or part.best.fitness < part.fitness:
                part.best = tools.clone(part)
            if not best or best.fitness < part.fitness:
                best = tools.clone(part) 
        for part in pop:
            tools.update(part, best)

        # Gather all the fitnesses in one list and print the stats
        stats.update(pop)
        for key, stat in stats.data.iteritems():
            print "  %s %s" % (key, stat[-1][0])
        print "  Best so far: %s - %s" % (best, best.fitness)
    
    return pop, stats, best

if __name__ == "__main__":
    main()

