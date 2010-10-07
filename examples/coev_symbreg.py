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
from eap import toolbox
from eap import gp

# gp_symbreg already defines some usefull structures
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
tools_ga.register("individual", creator.IndGA, content_init=tools_ga.float, size_init=10)
tools_ga.register("population", list, content_init=tools_ga.individual, size_init=200)

tools_ga.register("select", toolbox.selTournament, tournsize=3)
tools_ga.register("mate", toolbox.cxTwoPoints)
tools_ga.register("mutate", toolbox.mutGaussian, mu=0, sigma=0.01, indpb=0.05)

tools_gp = gp_symbreg.tools

if __name__ == "__main__":

    pop_ga = tools_ga.population()
    pop_gp = tools_gp.population()
    
    best_ga = toolbox.selRandom(pop_ga, 1)[0]
    best_gp = toolbox.selRandom(pop_gp, 1)[0]
    
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
                
        best_ga = toolbox.selBest(pop_ga, 1)[0]
        best_gp = toolbox.selBest(pop_gp, 1)[0]    
    
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop_ga]
        length = len(pop_ga)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std_dev = abs(sum2 / length - mean**2)**0.5
            
        print "--GA Population--"
        print "  Min %f" % min(fits)
        print "  Max %f" % max(fits)
        print "  Avg %f" % (mean)
        print "  Std %f" % std_dev
        
        fits = [ind.fitness.values[0] for ind in pop_gp]    
        print "--GP Population--"
        print "  Min %f" % min(fits)
        print "  Max %f" % max(fits)
        length = len(pop_gp)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std_dev = abs(sum2 / length - mean**2)**0.5
        print "  Avg %f" % (mean)
        print "  Std %f" % std_dev

    print "Best individual GA is %s, %s" % (best_ga, best_ga.fitness.values)
    print "Best individual GP is %s, %s" % (gp.evaluate(best_gp), best_gp.fitness.values)
