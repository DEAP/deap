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
    """Random test objective function.
    
    :math:`f_{\\text{Rand}}(\mathbf{x}) = \\text{\\texttt{random}}(0,1)`
    """
    return random.random(),
    
def plane(individual):
    """Plane test objective function.
    
    :math:`f_{\\text{Plane}}(\mathbf{x}) = x_0`
    """
    return individual[0],

def sphere(individual):
    """Sphere test objective function.
    
    :math:`f_{\\text{Sphere}}(\mathbf{x}) = \sum_{i=1}^Nx_i^2`
    """
    return sum(gene * gene for gene in individual),

def cigar(individual):
    """Cigar test objective function.
    
    :math:`f_{\\text{Cigar}}(\mathbf{x}) = x_0^2 + 10^6\\sum_{i=1}^N\,x_i^2`
    """
    return individual[0]**2 + 1e6 * sum(gene * gene for gene in individual),

def rosenbrock(individual):  
    """Rosenbrock test objective function.
    
    :math:`f_{\\text{Rosenbrock}}(\\mathbf{x}) = \\sum_{i=1}^{N-1} (1-x_i)^2 + 100 (x_{i+1} - x_i^2 )^2`
    
    .. plot:: _scripts/rosenbrock.py
       :width: 67 %
    """
    return sum(100 * (x * x - y)**2 + (1. - x)**2 \
                   for x, y in zip(individual[:-1], individual[1:])),

def h1(individual):
    """ Simple two-dimensional function containing several local maxima,
    H1 has a unique maximum value of 2.0 at the point (8.6998, 6.7665).
    From : The Merits of a Parallel Genetic Algorithm in Solving Hard 
    Optimization Problems, A. J. Knoek van Soest and L. J. R. Richard 
    Casius, J. Biomech. Eng. 125, 141 (2003)
    
    :math:`f_{\\text{H1}}(x_1, x_2) = \\frac{\sin(x_1 - \\frac{x_2}{8})^2 + \
            \\sin(x_2 + \\frac{x_1}{8})^2}{\\sqrt{(x_1 - 8.6998)^2 + \
            (x_2 - 6.7665)^2} + 1}`
    
    .. plot:: _scripts/h1.py
       :width: 67 %
    """
    num = (sin(individual[0] - individual[1] / 8))**2 + (sin(individual[1] + individual[0] / 8))**2
    denum = ((individual[0] - 8.6998)**2 + (individual[1] - 6.7665)**2)**0.5 + 1
    return num / denum,

 # 
# Multimodal
def ackley(individual):
    """Ackley test objective function.
    
    :math:`f_{\\text{Ackley}}(\\mathbf{x}) = 20 - 20\cdot\exp\left(-0.2\sqrt{\\frac{1}{N} \
                            \sum_{i=1}^N x_i^2} \\right)\
                            + e - \
                            \exp\left(\\frac{1}{N}\sum_{i=1}^N \\cos(2\pi x_i) \
                            \\right)`
                            
    .. plot:: _scripts/ackley.py
       :width: 67 %
    """
    N = len(individual)
    return 20 - 20 * exp(-0.2*sqrt(1.0/N * sum(x**2 for x in individual))) \
            + e - exp(1.0/N * sum(cos(2*pi*x) for x in individual)),
            
def bohachevsky(individual):
    """Bohachevsky test objective function
    
    :math:`f_{\\text{Bohachevsky}}(\mathbf{x}) = \sum_{i=1}^{N-1}(x_i^2 + 2x_{i+1}^2 - \
                        0.3\cos(3\pi x_i) - 0.4\cos(4\pi x_{i+1}) + 0.7)`
    
    .. plot:: _scripts/bohachevsky.py
       :width: 67 %
    """
    return sum(x**2 + 2*x1**2 - 0.3*cos(3*pi*x) - 0.4*cos(4*pi*x1) + 0.7 
                for x, x1 in zip(individual[:-1], individual[1:])),

def griewank(individual):
    """Griewank test objective function
    
    :math:`f_{\\text{Griewank}}(\\mathbf{x}) = \\frac{1}{4000}\\sum_{i=1}^N\,x_i^2 - \
                        \prod_{i=1}^N\\cos\\left(\\frac{x_i}{\sqrt{i}}\\right) + 1`
    
    .. plot:: _scripts/bohachevsky.py
       :width: 67 %
    """
    return 1.0/4000.0 * sum(x**2 for x in individual) - \
        reduce(mul, (cos(x/sqrt(i+1.0)) for i, x in enumerate(individual)), 1) + 1,
            
def rastrigin(individual):
    """Rastrigin test objective function.
    
    :math:`f_{\\text{Rastrigin}}(\\mathbf{x}) = 10N \sum_{i=1}^N x_i^2 - 10 \\cos(2\\pi x_i)`
    
    .. plot:: _scripts/rastrigin.py
       :width: 67 %
    """     
    return 10 * len(individual) + sum(gene * gene - 10 * \
                        cos(2 * pi * gene) for gene in individual),

def rastrigin_scaled(individual):
    """Scaled Rastrigin test objective function
    
    :math:`f_{\\text{RastScaled}}(\mathbf{x}) = 10N + \sum_{i=1}^N \
        \left(10^{\left(\\frac{i-1}{N-1}\\right)} x_i \\right)^2 x_i)^2 - \
        10\cos\\left(2\\pi 10^{\left(\\frac{i-1}{N-1}\\right)} x_i \\right)`
    """
    N = len(individual)
    return 10*N + sum((10**(i/(N-1))*x)**2 - 
                      10*cos(2*pi*10**(i/(N-1))*x) for i, x in enumerate(individual)),

def rastrigin_skew(individual):
    """Scaled Rastrigin test objective function
    
     :math:`f_{\\text{RastSkew}}(\mathbf{x}) = 10N \sum_{i=1}^N \left(y_i^2 - 10 \\cos(2\\pi x_i)\\right)`
        
     :math:`\\text{with } y_i = \
                            \\begin{cases} \
                                10\\cdot x_i & \\text{ if } x_i > 0,\\\ \
                                x_i & \\text{ otherwise } \
                            \\end{cases}`
    """
    N = len(individual)
    return 10*N + sum((10*x if x > 0 else x)**2 
                    - 10*cos(2*pi*(10*x if x > 0 else x)) for x in individual),
def schaffer(individual):
    """Schaffer test objective function.
    
    :math:`f_{\\text{Schaffer}}(\mathbf{x}) = \sum_{i=1}^{N-1} (x_i^2+x_{i+1}^2)^{0.25} \cdot \
                        \\left[ \sin^2(50\cdot(x_i^2+x_{i+1}^2)^{0.10}) + 1.0 \
                        \\right]`
    """
    return sum((x**2+x1**2)**0.25 * ((sin(50*(x**2+x1**2)**0.1))**2+1.0) 
                for x, x1 in zip(individual[:-1], individual[1:])),

def schwefel(individual):
    """Schwefel test objective function.
    
    :math:`f_{\\text{Schwefel}}(\mathbf{x}) = 418.9828872724339\cdot N - \
            \sum_{i=1}^N\,x_i\sin\\left(\sqrt{|x_i|}\\right)`
    """    
    N = len(individual)
    return 418.9828872724339*N-sum(x*sin(sqrt(abs(x))) for x in individual),

def himmelblau(individual):
    """The Himmelblau's function is multimodal with 4 defined minimums in 
    :math:`[-6, 6]^2`.
    
    :math:`f_{\\text{Himmelblau}}(x_1, x_2) = (x_1^2 + x_2 - 11)^2 + (x_1 + x_2^2 -7)^2`
    
    .. plot:: _scripts/himmelblau.py
        :width: 67 %
    """
    return (individual[0] * individual[0] + individual[1] - 11)**2 + \
        (individual[0] + individual[1] * individual[1] - 7)**2,

# Multiobjectives
def kursawe(individual):
    """Kursawe multiobjective function.
    
    :math:`f_{\\text{Kursawe}1}(\\mathbf{x}) = \\sum_{i=1}^{N-1} -10 e^{-0.2 \\sqrt{x_i^2 + x_{i+1}^2} }`
    
    :math:`f_{\\text{Kursawe}2}(\\mathbf{x}) = \\sum_{i=1}^{N} |x_i|^{0.8} + 5 \\sin(x_i^3)`

    .. plot:: _scripts/kursawe.py
       :width: 100 %
    """
    f1 = sum(-10 * exp(-0.2 * sqrt(x * x + y * y)) for x, y in zip(individual[:-1], individual[1:]))
    f2 = sum(abs(x)**0.8 + 5 * sin(x * x * x) for x in individual)
    return f1, f2