from __future__ import division
from collections import defaultdict

def mean(seq):
    """Returns the arithmetic mean of the sequence *seq* = 
    :math:`\{x_1,\ldots,x_n\}` as :math:`A = \\frac{1}{n} \sum_{i=1}^n x_i`.
    """
    return sum(seq) / len(seq)

def median(seq):
    """Returns the median of *seq* - the numeric value separating the higher half 
    of a sample from the lower half. If there is an even number of elements in 
    *seq*, it returns the mean of the two middle values.
    """
    sseq = sorted(seq)
    length = len(seq)
    if length % 2 == 1:
        return sseq[int((length - 1) / 2)]
    else:
        return (sseq[int((length - 1) / 2)] + sseq[int(length / 2)]) / 2

def var(seq):
    """Returns the variance :math:`\sigma^2` of *seq* = 
    :math:`\{x_1,\ldots,x_n\}` as
    :math:`\sigma^2 = \\frac{1}{N} \sum_{i=1}^N (x_i - \\mu )^2`,
    where :math:`\\mu` is the arithmetic mean of *seq*.
    """
    return abs(sum(x*x for x in seq) / len(seq) - mean(seq)**2)

def std_dev(seq):
    """Returns the square root of the variance :math:`\sigma^2` of *seq*.
    """
    return var(seq)**0.5

class Stats(object):
    """
    """
    def __init__(self, key=lambda x: x):
        self.key = key
        self.functions = {}
        self.data = defaultdict(list)

    def register(self, name, function):
        self.functions[name] = function
    
    def update(self, seq):
        # Transpose the values
        values = zip(*(self.key(elem) for elem in seq))
        for key, func in self.functions.items():
            self.data[key].append(map(func, values))
