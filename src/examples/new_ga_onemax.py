
import eap.base as base
import eap.toolbox as toolbox

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(1.0,))
lTools.register('individual', base.Individual, size=100,
                fitness=lTools.fitness, generator=base.booleanGenerator())
lTools.register('population', base.Population, size=300,
                generator=lTools.individual)

def evalOneMax(individual):
    if not individual.mFitness.isValid():
        individual.mFitness.append(individual.count(True))

lTools.register('evaluate', evalOneMax)
lTools.register('crossover', toolbox.twoPointsCx)
lTools.register('mutate', toolbox.flipBitMut, flipIndxPb=0.05)
lTools.register('select', toolbox.tournSel, tournSize=3)

lPop = lTools.population()

CXPB, MUTPB, NGEN = (0.5, 0.2, 40)

# Begin the evolution
for g in range(NGEN):
    print 'Generation', g

    lPop[:] = lTools.select(lPop, n=len(lPop))

    # Apply crossover and mutation
    for i in xrange(1, len(lPop), 2):
        if random.random() < CXPB:
            lPop[i - 1], lPop[i] = lTools.crossover(lPop[i - 1], lPop[i])
    for i in xrange(len(lPop)):
        if random.random() < MUTPB:
            lPop[i] = lTools.mutate(lPop[i])

    # Evaluate the population
    map(lTools.evaluate, lPop)

    # Gather all the fitnesses in one list and print the stats
    lFitnesses = [lInd.mFitness[0] for lInd in lPop]
    print '\tMin Fitness :', min(lFitnesses)
    print '\tMax Fitness :', max(lFitnesses)
    print '\tMean Fitness :', sum(lFitnesses)/len(lFitnesses)

print 'End of evolution'