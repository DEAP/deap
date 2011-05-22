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

from eap import base
from eap import operators
from eap import creator
from eap import toolbox

from eap import benchmarks

import random
import array

# Differential evolution parameters
NDIM = 10
NP = 300
NGEN = 200
CR = 0.25
F = 1

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

tools = toolbox.Toolbox()
tools.register("attr_float", random.uniform, -3, 3)
tools.register("individual", toolbox.fill_repeat, creator.Individual, tools.attr_float, dim=NDIM)
tools.register("population", toolbox.fill_repeat, list, tools.individual, dim=NP)
tools.register("select", operators.selRandom, n=3)
tools.register("evaluate", benchmarks.rastrigin)

stats = operators.Stats(lambda ind: ind.fitness.values)
stats.register("Avg", operators.mean)
stats.register("Std", operators.std_dev)
stats.register("Min", min)
stats.register("Max", max)

def main():
    pop = tools.population();
    hof = operators.HallOfFame(1)
    
    # Evaluate the individuals
    fitnesses = tools.map(tools.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    for g in range(NGEN):
        for k, agent in enumerate(pop):
            a,b,c = tools.select(pop)
            y = tools.clone(agent)
            index = random.randrange(NDIM)
            for i, value in enumerate(agent):
                if i == index or random.random() < CR:
                    y[i] = a[i] + F*(b[i]-c[i])
            y.fitness.values = tools.evaluate(y)
            if y.fitness > agent.fitness:
                pop[k] = y
        hof.update(pop)
        stats.update(pop)
        
        print "Generation", g 
        print stats
            
    print "Best individual is ", hof[0], hof[0].fitness.values[0]
            
if __name__ == "__main__":
    main()
