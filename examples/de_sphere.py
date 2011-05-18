from eap import base
from eap import operators
from eap import creator
from eap import toolbox

import random

# Differential evolution parameters
NDIM = 10
NP = 300
NGEN = 200
CR = 0.25
F = 1

def sphere(individual):
    return sum(value**2 for value in individual),

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

tools = toolbox.Toolbox()
tools.register("attr_float", random.uniform, -3, 3)
tools.register("individual", creator.Individual, toolbox.Repeat(tools.attr_float, NDIM))
tools.register("population", list, toolbox.Repeat(tools.individual, NP))
tools.register("select", operators.selRandom, n=3)
tools.register("evaluate", sphere)

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
        for key, stat in stats.data.iteritems():
            print "  %s %s" % (key, ", ".join(map(str, stat[-1])))
            
    print "Best individual is ", hof[0], hof[0].fitness.values[0]
            
if __name__ == "__main__":
    main()
