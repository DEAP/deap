import random
import operator

import numpy as np
from deap import tools

def sort_index(array):
    """Sort array index in assending order.

    :params array: An array to be sorted.
    :returns: An index array sorted in assending order for given array.
    """
    index = [i for i in range(len(array))]
    for i in range(1, len(array)):
        for j in range(i):
            if array[index[i]] < array[index[j]]:
                temp = index[i]
                for k in range(i-1, j-1, -1):
                    index[k+1] = index[k]
                index[j] = temp
                break
    return index

class MOEAD:
    """Implementation of MOEA/D.
    """
    def __init__(self, population, toolbox, weights, neighbour_size,
                 scalar_method, cxpb, mutpb, ngen, stats, verbose):
        self.population = population
        self.toolbox = toolbox
        self.weights = np.array(weights)
        self.neighbour_size = neighbour_size
        self.scalar_method = scalar_method
        self.cxpb = cxpb
        self.mutpb = mutpb
        self.ngen = ngen
        self.stats = stats
        self.verbose = verbose

        if hasattr(toolbox, 'improve'):
            self.improve = self.toolbox.improve
        else:
            self.improve = self.noop_improve

        if self.scalar_method == 'weightedSum':
            self.scalarize_objective = self.weighted_sum
        elif self.scalar_method == 'tchebycheff':
            self.scalarize_objective = self.tchebycheff
        else:
            raise ValueError('unknown scalar method')

    def run(self):
        """Execute MOEA/D.

        :returns: The external population
        :returns: A class:`~deap.tools.Logbook` with the statistics of the
                  evolution
        """
        self.logbook = tools.Logbook()
        logbook_header  = ['gen', 'nevals']
        logbook_header += (self.stats.fields if self.stats else [])
        self.logbook.header = logbook_header

        # Step 1)
        self.initialize()
        npop = len(self.population)

        record = self.stats.compile(self.population) if self.stats else {}
        self.logbook.record(gen=0, nevals=npop, **record)
        if self.verbose:
            print self.logbook.stream

        # Step 2)
        for i in range(self.ngen):
            for j in range(npop):
                self.update(j)

            record = self.stats.compile(self.population) if self.stats else {}
            self.logbook.record(gen=i+1, nevals=npop, **record)
            if self.verbose:
                print self.logbook.stream

        return self.EP, self.logbook

    def initialize(self):
        """Step 1) Initialization.
        """

        # Step 1.1)
        self.EP = []

        # Step 1.2)
        self.initialize_neighbour()

        # Step 1.3)
        # Generate an initial population at this step in the paper.
        # But this implementation assumes population as argument.

        # Step 1.4)
        self.ideal_point = []
        for w in self.population[0].fitness.weights:
            if w > 0:
                # Initialize very small value for maximize
                self.ideal_point.append(-1.0e+30)
            else:
                # Initialize very large value for minimize
                self.ideal_point.append(1.0e+30)

        for ind in self.population:
            ind.fitness.values = self.toolbox.evaluate(ind)
            self.update_reference(ind)

    def initialize_neighbour(self):
        """Step 1.2) Compute Euclidean distances between any two weight vectors
        and then work out the T closest weight vectors to each weight vector.
        """
        self.neighbour_table = []
        npop = len(self.population)
        distance_matrix = np.zeros((npop, npop))
        for i in range(npop):
            for j in range(i+1, npop):
                distance = np.linalg.norm(self.weights[i] - self.weights[j])
                distance_matrix[j, i] = distance_matrix[i, j] = distance

        for i in range(npop):
            index = sort_index(distance_matrix[i])
            self.neighbour_table.append(index[:self.neighbour_size])

    def update(self, i):
        """Step 2) Update.

        :params i: An index of subproblem.
        """
        offspring = self.generate_offspring(i)
        offspring = self.improve(i, offspring)
        offspring.fitness.values = self.toolbox.evaluate(offspring)
        self.update_reference(offspring)
        self.update_neighbours(i, offspring)
        self.update_EP(offspring)

    def generate_offspring(self, i):
        """Step 2.1) Reproduction.

        :params i: An index of subproblem.
        """
        neighbour_table = self.neighbour_table[i][:]
        # Select neighbour but not i
        neighbour_table.remove(i)
        k = random.choice(neighbour_table)
        # Select neighbour but not i, k
        neighbour_table.remove(k)
        l = random.choice(neighbour_table)

        c1 = self.population[k]
        c2 = self.population[l]

        choice = random.random()
        if choice < self.cxpb:
            c1 = self.toolbox.clone(c1)
            c2 = self.toolbox.clone(c2)
            c1, c2 = self.toolbox.mate(c1, c2)
            del c1.fitness.values
        choice = random.random()
        if choice < self.mutpb:
            c1 = self.toolbox.clone(c1)
            c1, = self.toolbox.mutate(c1)
            del c1.fitness.values
        # Ignore one individual. Bad idea?
        offspring = c1

        return offspring

    def noop_improve(self, i, offspring):
        """Step 2.2) Improvement.
        No improvement default. Register :meth:`toolbox.improve` for problem
        specific improvement.

        :params i: An index of subproblem.
        :params offspring: individual to improve.
        :returns: improved individual.
        """
        return offspring

    def update_reference(self, ind):
        """Step 2.3) Uodate of z.
        Also use by Step 1.4) initialize z.

        :params ind: An individual that maybe update ideal point.
        """
        for i in range(len(ind.fitness.values)):
            if ind.fitness.weights[i] > 0:
                if ind.fitness.values[i] > self.ideal_point[i]:
                    self.ideal_point[i] = ind.fitness.values[i]
            else:
                if ind.fitness.values[i] < self.ideal_point[i]:
                    self.ideal_point[i] = ind.fitness.values[i]

    def update_neighbours(self, i, offspring):
        """Step 2.4) Update of Neighbouring solutions.

        :params i: An index of subproblem.
        :params offspring: An individual that maybe update neighbour.
        """
        for j in range(self.neighbour_size):
            weight_index = self.neighbour_table[i][j]
            sol = self.population[weight_index]
            d = self.calculate_scalar(weight_index, offspring)
            e = self.calculate_scalar(weight_index, sol)
            if d < e:
                self.population[weight_index] = self.toolbox.clone(offspring)

    def calculate_scalar(self, weight_index, ind):
        """Calculate scalar value for individual.

        :params weight_index: An index of weight vector.
        :params ind: An indivudlal to calculate scalar value.
        :returns: Scalalized fitness value.
        """
        weight = self.weights[weight_index]
        return self.scalarize_objective(weight, ind)

    def weighted_sum(self, weight, ind):
        """Calculate scalar value using Weighted Sum Approch.

        :params weight: A weight vector.
        :params ind: An indivudlal to calculate scalar value.
        :returns: Scalalized fitness value.
        """
        return np.sum(weight * ind.fitness.values)

    def tchebycheff(self, weight, ind):
        """Calculate scalar value using Tchebycheff Approch.

        :params weight: A weight vector.
        :params ind: An indivudlal to calculate scalar value.
        :returns: Scalalized fitness value.
        """
        max_fun = -1.0e+30
        for f, z, w in zip(ind.fitness.values, self.ideal_point, weight):
            diff = abs(f - z)
            if w == 0:
                feval = 0.00001 * diff
            else:
                feval = w * diff
            if feval > max_fun:
                max_fun = feval
        return max_fun

    def update_EP(self, offspring):
        """Step 2.5) Update of EP.

        :params offspring: An individual that maybe add to EP.
        """

        # Setup condition list for each objective
        cond = [operator.gt if w > 0 else operator.lt
                for w in offspring.fitness.weights]

        nobj = len(cond)
        def dominated(a, b):
            # Dominated means all conditions are True
            return sum([
                c(a, b)
                for a, b, c in zip(a.fitness.values, b.fitness.values, cond)
            ]) == nobj

        # Remove from EP if all vectors dominated by offspring
        self.EP = [ind for ind in self.EP if not dominated(offspring, ind)]

        # Add offspring to EP if no vectors in EP dominate offspring
        for ind in self.EP:
            if offspring == ind:
                return
            if dominated(ind, offspring):
                return
        self.EP.append(offspring)
