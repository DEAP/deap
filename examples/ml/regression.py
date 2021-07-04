#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import numpy.linalg as LA
from deap import base, creator, tools, algorithms

from utils import cxTwoPointCopy

from sklearn.base import RegressorMixin
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge

class GALinearRegression(LinearRegression):
    '''Linear Regression

    solve Xp = y, with min_p ||Xp-y|| + a||p||, a>=0
    '''

    alpha = 1 # Regularization strength

    def fit(self, X, y, *args, **kwargs):
        self.intercept_ = np.mean(y)
        pop, self.logbook = self.config(X,y)()
        self.coef_ = tools.selBest(pop,1)[0]
        return self

    def config(self, X, y):

        creator.create("FitnessMin", base.Fitness, weights=(-1,))
        creator.create("Individual", np.ndarray, fitness=creator.FitnessMin)

        IND_SIZE = X.shape[1]
        toolbox = base.Toolbox()
        toolbox.register("gene", np.random.random)
        toolbox.register("coef", tools.initRepeat, creator.Individual,
                         toolbox.gene, n=IND_SIZE)
        toolbox.register("population", tools.initRepeat, list, toolbox.coef)

        toolbox.register("mate", cxTwoPointCopy)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.1)
        toolbox.register("select", tools.selTournament, tournsize=3)

        def evaluate(coef):
            return LA.norm(X @ coef-y+self.intercept_) + GALinearRegression.alpha * LA.norm(coef, 1),

        toolbox.register("evaluate", evaluate)

        def ga(pop=None):
            if pop is None:
                pop = toolbox.population(n=200)
            pop, logbook = algorithms.eaSimple(pop, toolbox=toolbox, cxpb=0.55, mutpb=0.11, ngen=500, verbose=False)
            return pop, logbook
        return ga

    def perf(self, n=10, *args, **kwargs):
        """Check the performance by running it several times
        
        Arguments:
            n {int} -- running times
        
        Returns:
            number -- mean time
        """
        import time
        times = []
        for _ in range(n):
            time1 = time.perf_counter()
            self.fit(*args, **kwargs)
            time2 = time.perf_counter()
            times.append(time2 - time1)
        return np.mean(times)

if __name__ == '__main__':
    
    import pandas as pd
    data = pd.read_csv('winequality.csv')
    keys = data.columns
    A = data[keys[:-1]].values # the rest is input
    B = data[keys[-1]].values  # the last colunm is ouput
    A, A_test, B, B_test = train_test_split(A, B, test_size=0.2)

    gar = GALinearRegression()
    gar.fit(A, B)
    B_pred = gar.predict(A_test)
    print(f'GA solution(test score): {gar.coef_} ({gar.score(A_test, B_test)})')

    r = Ridge()
    r.fit(A, B)
    B_pred = r.predict(A_test)
    print(f'Ridge solution(test score): {r.coef_} ({r.score(A_test, B_test)})')
