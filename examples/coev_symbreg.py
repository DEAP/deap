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

import random

from eap import base
from eap import creator
from eap import gp
from eap import operators
from eap import toolbox

# gp_symbreg already defines some useful structures
import gp_symbreg

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("IndGA", list, fitness=creator.FitnessMax)

def refFunc(x):
    return x**4 + x**3 + x**2 + x
    
def evalSymbReg(expr, data):
    # Transform the tree expression in a callable function
    func = tools_gp.lambdify(expr=expr)
    # Evaluate the sum of squared difference between the expression
    # and the real function : x**4 + x**3 + x**2 + x
    values = data
    diff_func = lambda x: (func(x)-refFunc(x))**2
    diff = sum(map(diff_func, values))
    return diff,

tools_ga = toolbox.Toolbox()

tools_ga.register("float", random.uniform, -1, 1)
tools_ga.register("individual", creator.IndGA, toolbox.Repeat(tools_ga.float, 10))
tools_ga.register("population", list, toolbox.Repeat(tools_ga.individual, 200))

tools_ga.register("select", operators.selTournament, tournsize=3)
tools_ga.register("mate", operators.cxTwoPoints)
tools_ga.register("mutate", operators.mutGaussian, mu=0, sigma=0.01, indpb=0.05)

tools_gp = gp_symbreg.tools

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    pop_ga = tools_ga.population()
    pop_gp = tools_gp.population()
    
    stats_ga = tools_ga.clone(stats_t)
    stats_gp = tools_gp.clone(stats_t)
    
    best_ga = operators.selRandom(pop_ga, 1)[0]
    best_gp = operators.selRandom(pop_gp, 1)[0]
    
    for ind in pop_gp:
        ind.fitness.values = evalSymbReg(ind, best_ga)  
    
    for ind in pop_ga:
        ind.fitness.values = evalSymbReg(best_gp, ind)
    
    CXPB, MUTPB, NGEN = 0.5, 0.2, 50
    
    # Begin the evolution
    for g in range(NGEN):
        print "-- Generation %i --" % g
    
        # Select and clone the offsprings
        off_ga = tools_ga.select(pop_ga, n=len(pop_ga))
        off_gp = tools_gp.select(pop_gp, n=len(pop_gp))
        off_ga = [tools_ga.clone(ind) for ind in off_ga]        
        off_gp = [tools_gp.clone(ind) for ind in off_gp]
    
    
        # Apply crossover and mutation
        for ind1, ind2 in zip(off_ga[::2], off_ga[1::2]):
            if random.random() < CXPB:
                tools_ga.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values
    
        for ind1, ind2 in zip(off_gp[::2], off_gp[1::2]):
            if random.random() < CXPB:
                tools_gp.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values
    
        for ind in off_ga:
            if random.random() < MUTPB:
                tools_ga.mutate(ind)
                del ind.fitness.values
    
        for ind in off_gp:
            if random.random() < MUTPB:
                tools_gp.mutate(ind)
                del ind.fitness.values
    
        # Evaluate the individuals with an invalid fitness     
        for ind in off_ga:
            if not ind.fitness.valid:
               ind.fitness.values = evalSymbReg(best_gp, ind)
        
        for ind in off_gp:
            if not ind.fitness.valid:
                ind.fitness.values = evalSymbReg(ind, best_ga)
                
        # Replace the old population by the offsprings
        pop_ga = off_ga
        pop_gp = off_gp
        
        stats_ga.update(pop_ga)
        stats_gp.update(pop_gp)
        
        best_ga = operators.selBest(pop_ga, 1)[0]
        best_gp = operators.selBest(pop_gp, 1)[0]    
    
        print "  -- GA statistics --"
        for key, stat in stats_ga.data.iteritems():
            print "  %s %s" % (key, stat[-1][0])
        print "  -- GP statistics --"        
        for key, stat in stats_gp.data.iteritems():
            print "  %s %s" % (key, stat[-1][0])            

    print "Best individual GA is %s, %s" % (best_ga, best_ga.fitness.values)
    print "Best individual GP is %s, %s" % (gp.evaluate(best_gp), best_gp.fitness.values)

    return pop_ga, pop_gp, stats_ga, stats_gp, best_ga, best_gp

if __name__ == "__main__":
    main()
