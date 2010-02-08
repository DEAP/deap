
import eap.base as base
import eap.algorithms as algorithms
import eap.specialized as specialized
import eap.toolbox as toolbox

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(1.0,))
lTools.register('individual', specialized.IndividualArray, typecode='b', size=100,
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
algorithms.simpleGA(lTools, lPop, 0.5, 0.2, 40)