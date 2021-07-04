#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

def unique(pop):
    popu = [pop[0]]
    for ind in pop[1:]:
        for ind1 in popu:
            if ind == ind1:
                break
        else:
            popu.append(ind)
    return popu

def clean(pop):
    popc = [pop[0]]
    for ind in pop[1:]:
        flag = True
        for ind1 in popc:
            if ind < ind1:
                popc.remove(ind1)
            elif ind > ind1 or ind == ind1:
                flag = False
                break
        if flag:
            popc.append(ind)
    return popc


def cxTwoPointCopy(ind1, ind2):
    """Execute a two points crossover with copy on the input individuals.
    see https://deap.readthedocs.io/en/master/examples/ga_onemax_numpy.html
    """
    size = len(ind1)
    cxpoint1 = np.random.randint(1, size)
    cxpoint2 = np.random.randint(1, size - 1)
    if cxpoint2 >= cxpoint1:
        cxpoint2 += 1
    else: # Swap the two cx points
        cxpoint1, cxpoint2 = cxpoint2, cxpoint1

    ind1[cxpoint1:cxpoint2], ind2[cxpoint1:cxpoint2] \
        = ind2[cxpoint1:cxpoint2], ind1[cxpoint1:cxpoint2].copy()
        
    return ind1, ind2


def cxTwoPoint2DArray(ind1, ind2):
    """Execute a two points crossover with copy on the input individuals.
    see https://deap.readthedocs.io/en/master/examples/ga_onemax_numpy.html
    """
    m, n = ind1.shape
    if np.random.random()<0.5:
        cxpoint1 = np.random.randint(1, m)
        cxpoint2 = np.random.randint(1, m - 1)
        if cxpoint2 >= cxpoint1:
            cxpoint2 += 1
        else: # Swap the two cx points
            cxpoint1, cxpoint2 = cxpoint2, cxpoint1

        ind1[cxpoint1:cxpoint2], ind2[cxpoint1:cxpoint2] \
            = ind2[cxpoint1:cxpoint2], ind1[cxpoint1:cxpoint2].copy()
    else:
        cxpoint1 = np.random.randint(1, m)
        cxpoint2 = np.random.randint(1, m - 1)
        if cxpoint2 >= cxpoint1:
            cxpoint2 += 1
        else: # Swap the two cx points
            cxpoint1, cxpoint2 = cxpoint2, cxpoint1

        ind1[:, cxpoint1:cxpoint2], ind2[:, cxpoint1:cxpoint2] \
            = ind2[:, cxpoint1:cxpoint2], ind1[:, cxpoint1:cxpoint2].copy()
        
    return ind1, ind2
