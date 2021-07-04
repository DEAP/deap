#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math, random

from deap import base, creator, tools, algorithms

def move(state, toolbox, T):
    """Transition of states
    
    Arguments:
        state {[type]} -- state of physical body
        toolbox {Toolbox} -- the boolbox in DEAP
        T {number} -- temperature
    
    Returns:
        a state
    """
    new_state = toolbox.clone(state)
    new_state, = toolbox.get_neighbour(new_state)
    new_state.fitness.values = toolbox.evaluate(new_state)
    D = new_state.fitness.values[0] - state.fitness.values[0]
    return metropolis(state, new_state, D, T)

def metropolis(state, new_state, D, T):
    """Metropolis rule
    
    Just a Bernoulli distribution
    
    Arguments:
        state {list|array} -- state of the physical body in annealing
        new_state {list|array} -- new state
        D,T {number} -- parameters for acceptance prob.
    
    Returns:
        state or new_state
    """
    if D > 0:
        p = min((1, math.exp(-D/T)))
        if random.random() <= p:
            return new_state
        else:
            return state
    else:
        return new_state

class Annealing:
    """Simulated Annealing algorithm
    """

    c = 0.99
    cc = 0.999
    nepoch = 50

    def __call__(self, state, toolbox, initT, ngen, stats=None, verbose=__debug__):
        """Simulated Annealing algorithm
        
        Arguments:
            state {list|array} -- state of the physical body in annealing
            toolbox {Toolbox} -- toolbox of DEAP
            initT {number} -- initial temperature
            ngen {int} -- number of generation
        
        Keyword Arguments:
            stats, verbose -- the same to GA
        
        Returns:
            state, logbook
        """

        logbook = tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

        # Evaluate the states with an invalid fitness
        if not state.fitness.valid:
            state.fitness.values = toolbox.evaluate(state)

        record = stats.compile([state]) if stats else {}
        logbook.record(gen=0, nevals=1, **record)
        if verbose:
            print(logbook.stream)

        # Begin the annealing process
        v = state.fitness.values
        for gen in range(1, ngen + 1):
            T = initT
            init = state[:]
            for epoch in range(Annealing.nepoch):
                new_state = move(state, toolbox, T)
                state = new_state
                T *= Annealing.cc ** epoch
            initT *= Annealing.c ** gen
            # Append the current state statistics to the logbook
            record = stats.compile([state]) if stats else {}
            logbook.record(gen=gen, nevals=1, **record)
        return state, logbook

annealing = Annealing()
