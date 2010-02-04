
from mpi4py import MPI
import eap.base as base
import eap.evolver as evolver
import eap.operators as operators

def distributedGA(evolver, population, cxPb, mutPb, nGen):
    # Evaluate the population
    map(evolver.evaluate, lPop)
    
    # Begin the evolution
    for g in range(nGen):
        print 'Generation', g
    
        lPop[:] = evolver.select(lPop, n=len(lPop))
    
        # Apply crossover and mutation
        for i in xrange(1, len(lPop), 2):
            if random.random() < cxPb:
                lPop[i - 1], lPop[i] = evolver.crossover(lPop[i - 1], lPop[i])
        for i in xrange(len(lPop)):
            if random.random() < mutPb:
                lPop[i] = evolver.mutate(lPop[i])
        
        lChilds = [dtm.spawn(evolver.evaluate, lInd) for lInd in lPop]
            
        lData = yield ('waitFor', lChilds)
        
        for i, lID in enumerate(lChilds):
            lPop[i].mFitness.append(lData[lID])
    
        # Gather all the fitnesses in one list and print the stats
        lFitnesses = [lInd.mFitness[0] for lInd in lPop]
        print '\tMin Fitness :', min(lFitnesses)
        print '\tMax Fitness :', max(lFitnesses)
        print '\tMean Fitness :', sum(lFitnesses)/len(lFitnesses)
        
    print 'End of evolution'


def evalOneMax(individual):
    if not individual.mFitness.isValid():
        yield individual.count(True))


if MPI.COMM_WORLD.Get_rank() == 0:
    evolver.register('fitness', base.Fitness, weights=(1.0,))
    evolver.register('individual', base.Individual, size=100,
                    fitness=evolver.fitness, generator=base.booleanGenerator())
    evolver.register('population', base.Population, size=300,
                    generator=evolver.individual)
    
    evolver.register('evaluate', evalOneMax)
    evolver.register('crossover', operators.twoPointsCx)
    evolver.register('mutate', operators.flipBitMut, flipIndxPb=0.05)
    evolver.register('select', operators.tournSel, tournSize=3)
    evolver.register('evolve', evolver.distributedGA)
    
    lPop = evolver.population()
    
    evolver.evolve(lPop, cxPb=0.5, mutPb=0.2, nGen=40)