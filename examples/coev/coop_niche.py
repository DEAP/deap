#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

"""This example contains the niching test from *Potter, M. and De Jong, K.,
2001, Cooperative Coevolution: An Architecture for Evolving Co-adapted
Subcomponents.* section 4.2.1. Varying the *TARGET_TYPE* in :math:`\\lbrace 
2, 4, 8 \\rbrace` will produce the results for the half-, quarter- and
eight-length schematas.
"""

import random
import numpy as np

from deap import algorithms, tools

import coop_base

IND_SIZE = coop_base.IND_SIZE
SPECIES_SIZE = coop_base.SPECIES_SIZE
TARGET_SIZE = 200
TARGET_TYPE = 2

def nicheSchematas(type, size):
    """Produce the desired schemata based on the type required, 2 for half
    length, 4 for quarter length and 8 for eight length.
    """
    rept = size // type
    return ["#" * (i*rept) + "1" * rept + "#" * ((type-i-1)*rept) for i in range(type)]

toolbox = coop_base.toolbox

def main(extended=True, verbose=True):
    target_set = []

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    logbook = tools.Logbook()
    logbook.header = "gen", "species", "evals", "std", "min", "avg", "max"

    ngen =50
    g = 0
    
    size = TARGET_SIZE // TARGET_TYPE
    schematas = nicheSchematas(TARGET_TYPE, IND_SIZE)
    L = len(schematas)
    for schemata in schematas:
        target_set.extend(toolbox.target_set(schemata, size))
    species=[toolbox.species() for _ in range(L)]  # set of populations

    # Init with a random representative for each species
    representatives = [random.choice(s) for s in species]
    
    while g < ngen:
        # Initialize a container for the next generation representatives
        next_repr = [None] * L
        for i, s in enumerate(species):
            # Vary the species individuals
            s = algorithms.varAnd(s, toolbox, 0.6, 1.0)
            
            r = representatives[:]
            for ind in s:
                r[i] = ind    # replace the i-th individual with an individual in the current specie
                ind.fitness.values = toolbox.evaluate(r, target_set)
            
            record = stats.compile(s)
            logbook.record(gen=g, species=i, evals=len(s), **record)
            
            if verbose: 
                print(logbook.stream)
            
            # Select the individuals
            species[i] = toolbox.select(s, len(s))  # Tournament selection
            next_repr[i] = toolbox.get_best(s)[0]   # Best selection
        
            g += 1
        representatives = next_repr

    if extended:
        for r in representatives:
            print("".join(map(str, r)))
    
if __name__ == "__main__":
    main()
