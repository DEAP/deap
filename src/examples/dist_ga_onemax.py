
from mpi4py import MPI
import eap.base as base
import eap.toolbox as toolbox

def distributedGA(toolbox, population, cxPb, mutPb, nGen):
    # Evaluate the population
    map(toolbox.evaluate, population)
    
    # Begin the evolution
    for g in range(nGen):
        print 'Generation', g
    
        lPop[:] = toolbox.select(lPop, n=len(population))
    
        # Apply crossover and mutation
        for i in xrange(1, len(lPop), 2):
            if random.random() < cxPb:
                population[i - 1], population[i] = toolbox.crossover(population[i - 1], population[i])
        for i, ind in enumerate(population):
            if random.random() < mutPb:
                lPop[i] = toolbox.mutate(ind)

        # Distribute the evaluation
        lChilds = [dtm.spawn(toolbox.evaluate, lInd) for lInd in population]
        lData = yield ('waitFor', lChilds)
        for i, lID in enumerate(lChilds):
            lPop[i].mFitness.append(lData[lID])
    
        # Gather all the fitnesses in one list and print the stats
        lFitnesses = [lInd.mFitness[0] for lInd in population]
        print '\tMin Fitness :', min(lFitnesses)
        print '\tMax Fitness :', max(lFitnesses)
        print '\tMean Fitness :', sum(lFitnesses)/len(lFitnesses)
        
    print 'End of evolution'


def evalOneMax(individual):
    if not individual.mFitness.isValid():
        yield individual.count(True))


if MPI.COMM_WORLD.Get_rank() == 0:
    lTools = toolbox.Toolbox()
    lTools.register('fitness', base.Fitness, weights=(1.0,))
    lTools.register('individual', base.Individual, size=100,\
                   fitness=lTools.fitness, generator=base.booleanGenerator())
    lTools.register('population', base.Population, size=300,\
                    generator=lTools.individual)

    lTools.register('evaluate', evalOneMax)
    lTools.register('crossover', toolbox.twoPointsCx)
    lTools.register('mutate', toolbox.flipBitMut, flipIndxPb=0.05)
    lTools.register('select', toolbox.tournSel, tournSize=3)

    lPop = lTools.population()
    dtm.spawn(distributedGA, lTools, lPop, 0.5, 0.2, 40)