# To change this template, choose Tools | Templates
# and open the template in the editor.

import eap.base

ind1 = eap.base.IndicesIndividual(5, eap.base.Fitness)
ind2 = eap.base.IndicesIndividual(5, eap.base.Fitness)

ind1.mFitness.fromlist([3, 4])
ind2.mFitness.fromlist([4, 4])

print type(ind1.mFitness)

lst = [ind1, ind2]
lst.sort()
lst.reverse()

print lst
