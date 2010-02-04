
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
lEvolver.register('evolve', evolver.simpleGA)

lPop = lEvolver.population()

# Evaluate the population
map(lEvolver.evaluate, lPop)

lEvolver.evolve(lEvolver, lPop, 0.5, 0.2, 40)