#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.


"""
Regroup typical EC benchmarks functions to import easily and benchmark
examples.
"""

import random
from math import sin, cos, pi, exp, e, sqrt
from operator import mul
from functools import reduce

# Unimodal
def rand(individual):
    """Random test objective function."""
    return random.random(),
    
def plane(individual):
    """Plane test objective function."""
    return individual[0],

def sphere(individual):
    """Sphere test objective function."""
    return sum(gene * gene for gene in individual),

def cigar(individual):
    """Cigar test objective function."""
    return individual[0]**2 + 1e6 * sum(gene * gene for gene in individual),

def rosenbrock(individual):  
    """Rosenbrock test objective function."""
    return sum(100 * (x * x - y)**2 + (1. - x)**2 \
                   for x, y in zip(individual[:-1], individual[1:])),

def h1(individual):
    """ Simple two-dimensional function containing several local maxima,
    H1 has a unique maximum value of 2.0 at the point (8.6998, 6.7665).
    From : The Merits of a Parallel Genetic Algorithm in Solving Hard 
    Optimization Problems, A. J. Knoek van Soest and L. J. R. Richard 
    Casius, J. Biomech. Eng. 125, 141 (2003)
    
    :math:`f(x_1, x_2) = \\frac{\sin(x_1 - \\frac{x_2}{8})^2 + 
    \\sin(x_2 + \\frac{x_1}{8})^2}{\\sqrt{(x_1 - 8.6998)^2 + 
    (x_2 - 6.7665)^2} + 1}`
    
    .. image:: _images/h1.*
       :width: 67 %
    """
    num = (sin(individual[0] - individual[1] / 8))**2 + (sin(individual[1] + individual[0] / 8))**2
    denum = ((individual[0] - 8.6998)**2 + (individual[1] - 6.7665)**2)**0.5 + 1
    return num / denum,


# Multimodal
def ackley(individual):
    """Ackley test objective function."""
    N = len(individual)
    return 20 - 20 * exp(-0.2*sqrt(1.0/N * sum(x**2 for x in individual))) \
            + e - exp(1.0/N * sum(cos(2*pi*x) for x in individual)),
            
def bohachevsky(individual):
    return sum(x**2 + 2*x1**2 - 0.3*cos(3*pi*x) - 0.4*cos(4*pi*x1) + 0.7 
                for x, x1 in zip(individual[:-1], individual[1:])),

def griewank(individual):
    return 1.0/4000.0 * sum(x**2 for x in individual) - \
        reduce(mul, (cos(x/sqrt(i+1.0)) for i, x in enumerate(individual)), 1) + 1,
            
def rastrigin(individual):
    """Rastrigin test objective function. Consider using ``lambda_ = 20 * N`` 
    for this test function.
    """     
    return 10 * len(individual) + sum(gene * gene - 10 * \
                        cos(2 * pi * gene) for gene in individual),

def rastrigin_scaled(individual):
    N = len(individual)
    return 10*N + sum((10**(i/(N-1))*x)**2 - 
                      10*cos(2*pi*10**(i/(N-1))*x) for x in individual),

def rastrigin_skew(individual):
    N = len(individual)
    return 10*N + sum((10*x if x > 0 else x)**2 
                    - 10*cos(2*pi*(10*x if x > 0 else x)) for x in individual),
def schaffer(individual):
    return sum((x**2+x1**2)**0.25 * ((sin(50*(x**2+x1**2)**0.1))**2+1.0) 
                for x, x1 in zip(individual[:-1], individual[1:])),

def schwefel(individual):
    N = len(individual)
    return 418.9828872724339*N-sum(x*sin(sqrt(abs(x))) for x in individual),

def himmelblau(individual):
    '''The Himmelblau's function is multimodal with 4 defined minimums in 
    :math:`[-6, 6]^2`.
    
    :math:`f(x_1, x_2) = (x_1^2 + x_2 - 11)^2 + (x_1 + x_2^2 -7)^2`
    
    .. image:: _images/himmelblau.*
       :width: 67 %
    
    '''
    return (individual[0] * individual[0] + individual[1] - 11)**2 + \
        (individual[0] + individual[1] * individual[1] - 7)**2,

# Multiobjectives
def kursawe(individual):
    """Kursawe multiobjective function.
    
    :math:`f_1(\\mathbf{x}) = \\sum_{i=1}^{N-1} -10 e^{-0.2 \\sqrt{x_i^2 + x_{i+1}^2}}`
    
    :math:`f_2(\\mathbf{x}) = \\sum_{i=1}^{N} |x_i|^{0.8} + 5 \\sin(x_i^3)`
    
    .. image:: _images/kursawe1.*
       :width: 48 %
    .. image:: _images/kursawe2.*
       :width: 48 %
    """
    f1 = sum(-10 * exp(-0.2 * sqrt(x * x + y * y)) for x, y in zip(individual[:-1], individual[1:]))
    f2 = sum(abs(x)**0.8 + 5 * sin(x * x * x) for x in individual)
    return f1, f2