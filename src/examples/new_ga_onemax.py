
import random
import eap.base as base
import eap.evolver as evolver
import eap.operators as operators

lEvolver = evolver.Evolver()
lEvolver.register('fitness', base.Fitness, weights=(1.0,))
lEvolver.register('individual', base.Individual, size=100,
                fitness=lEvolver.fitness, generator=base.booleanGenerator())
lEvolver.register('population', base.Population, size=300,
                generator=lEvolver.individual)
                
def evalOneMax(individual):
    if not individual.mFitness.isValid():
        individual.mFitness.append(individual.count(True))

lEvolver.register('evaluate', evalOneMax)
lEvolver.register('crossover', operators.twoPointsCx)
lEvolver.register('mutate', operators.flipBitMut, flipIndxPb=0.05)
lEvolver.register('select', operators.tournSel, tournSize=3)

lPop = lEvolver.population()

# Evaluate the population
map(lEvolver.evaluate, lPop)

CXPB, MUTPB, NGEN = (0.5, 0.2, 40)

# Begin the evolution
for g in range(NGEN):
    print 'Generation', g

    lPop[:] = lEvolver.select(lPop, n=len(lPop))

    # Apply crossover and mutation
    for i in xrange(1, len(lPop), 2):
        if random.random() < CXPB:
            lPop[i - 1], lPop[i] = lEvolver.crossover(lPop[i - 1], lPop[i])
    for i in xrange(len(lPop)):
        if random.random() < MUTPB:
            lPop[i] = lEvolver.mutate(lPop[i])

    # Evaluate the population
    map(lEvolver.evaluate, lPop)

    # Gather all the fitnesses in one list and print the stats
    lFitnesses = [lInd.mFitness[0] for lInd in lPop]
    print '\tMin Fitness :', min(lFitnesses)
    print '\tMax Fitness :', max(lFitnesses)
    print '\tMean Fitness :', sum(lFitnesses)/len(lFitnesses)

print 'End of evolution'