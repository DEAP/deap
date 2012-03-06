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

"""
Re-implementation of the `Moving Peak Benchmark 
<http://people.aifb.kit.edu/jbr/MovPeaks/>`_ by Jurgen Branke.
"""

import math
import itertools
import random

def cone(individual, position, height, width):
    """The cone peak function to be used with scenario 2 and 3.
    
    :math:`f(\mathbf{x}) = h - w \sqrt{\sum_{i=1}^N (x_i - p_i)^2}`
    
    """
    value = 0.0
    for x, p in zip(individual, position):
        value += (x - p)**2
    return height - width * math.sqrt(value)

def sphere(individual, position, height, width):
    value = 0.0
    for x, p in zip(individual, position):
        value += (x - p)**2
    return height * value

def function1(individual, position, height, width):
    """The function1 peak function to be used with scenario 1.
    
    :math:`f(\mathbf{x}) = \\frac{h}{1 + w \sqrt{\sum_{i=1}^N (x_i - p_i)^2}}`
    
    """
    value = 0.0
    for x, p in zip(individual, position):
        value += (x - p)**2
    return height / (1 + width * value)

class MovingPeaks:
    """The Moving Peaks Benchmark is a fitness function changing over time. It
    consists of a number of peaks, changing in height, width and location. The
    peaks function is given by *pfunc*, wich is either a function object or a
    list of function objects. The number of peaks is determined by *npeaks*,
    while the dimensionality of the search domain is *dim*. A basis function
    *bfunc* can also be given to act as static landscape (the default is no
    basis function). The argument *random* serves to grant an independent
    random number generator to the moving peaks so that the evolution is not
    influenced by number drawn by this object (the default uses random
    functions from the Python module :mod:`random`). Various other keyword
    parameters listed in the table below are required to setup the benchmark,
    default parameters are based on scenario 1 of this benchmark.
    
    =================== ================= =================================================================================================================
    Parameter           Default               Details
    =================== ================= =================================================================================================================
    ``pfunc``           :func:`function1` The peak function.
    ``npeaks``          5                 Number of peaks.
    ``min_coord``       0.0               Minimum coordinate for the centre of the peaks.
    ``max_coord``       100.0             Maximum coordinate for the centre of the peaks.
    ``min_height``      30.0              Minimum height of the peaks.
    ``max_height``      70.0              Maximum height of the peaks.
    ``uniform_height``  50.0              Starting height for all peaks, if ``uniform_height <= 0`` the initial height is set randomly for each peak.
    ``min_width``       0.0001            Minimum width of the peaks.
    ``max_width``       0.2               Maximum width of the peaks
    ``uniform_width``   0.1               Starting width for all peaks, if ``uniform_width <= 0`` the initial width is set randomly for each peak.
    ``lambda_``         0.0               Correlation between changes.
    ``move_severity``   1.0               The distance a single peak moves when peaks change.
    ``height_severity`` 7.0               The standard deviation of the change made to the height of a peak when peaks change.
    ``width_severity``  0.01              The standard deviation of the change made to the width of a peak when peaks change.
    =================== ================= =================================================================================================================
    
    Dictionnaries :data:`SCENARIO_1`, :data:`SCENARIO_2` and
    :data:`SCENARIO_3` of this module define the defaults for these
    parameters. For scenario 1, use :func:`function1` while for scenario 2 and
    3, use :func:`cone`. The scenario 3 requires a constant basis function
    which can be given as a lambda function ``lambda x: constant``.
    
    The following shows an example of scenario 1 with non uniform heights and
    widths.
    
    .. plot:: code/benchmarks/movingsc1.py
       :width: 67 %
    """
    def __init__(self, pfunc, npeaks, dim, bfunc=None, random=random, **kargs):
        try:
            assert len(pfunc) == npeaks, ("Iterable pfunc must contain npeaks peaks.")
            self.peaks_function = pfunc
        except TypeError:
            self.peaks_function = [f for f in itertools.repeat(pfunc, npeaks)]
        
        self.random = random
        self.basis_function = bfunc
        
        # The following default values are based on Scenario #1 as proposed
        # by Branke in its original implementation
        self.min_coord = kargs.get("min_coord", 0.0)
        self.max_coord = kargs.get("max_coord", 100.0)
        
        self.min_height = kargs.get("min_height", 30.0)
        self.max_height = kargs.get("max_height", 70.0)
        uniform_height = kargs.get("uniform_height", 50.0)
        
        self.min_width = kargs.get("min_width", 0.0001)
        self.max_width = kargs.get("max_width", 0.2)
        uniform_width = kargs.get("uniform_width", 0.1)
        
        self.lambda_ = kargs.get("lambda_", 0.0)
        self.move_severity = kargs.get("move_severity", 1.0)
        self.height_severity = kargs.get("height_severity", 7.0)
        self.width_severity = kargs.get("width_severity", 0.01)
        
        #def randUniform(min, max):
        #    return self.random.random()*(max - min) + min
        
        self.peaks_position = [[self.random.uniform(self.min_coord, self.max_coord) for _ in range(dim)] for _ in range(npeaks)]
        
        if uniform_height > 0:
            self.peaks_height = [uniform_height for _ in range(npeaks)]
        else:
            self.peaks_height = [self.random.uniform(self.min_height, self.max_height) for _ in range(npeaks)]
        
        if uniform_width > 0:
            self.peaks_width = [uniform_width for _ in range(npeaks)]
        else:
            self.peaks_width = [self.random.uniform(self.min_width, self.max_width) for _ in range(npeaks)]
        
        self.last_change_vector = [[self.random.random() - 0.5 for _ in range(dim)] for _ in range(npeaks)]
    
    def globalMaximum(self):
        """Returns the global maximum value and position."""
        # The global maximum is at one peak's position
        potential_max = list()
        for func, pos, height, width in zip(self.peaks_function,
                                            self.peaks_position,
                                            self.peaks_height,
                                            self.peaks_width):
            potential_max.append((func(pos, pos, height, width), pos))
        return max(potential_max)
    
    def maximums(self):
        """Returns all visible maximums value and position sorted with the
        global maximum first.
        """
        # The maximums are at the peaks position but might be swallowed by 
        # other peaks
        maximums = list()
        for func, pos, height, width in zip(self.peaks_function,
                                            self.peaks_position,
                                            self.peaks_height,
                                            self.peaks_width):
            val = func(pos, pos, height, width)
            if val >= self.__call__(pos)[0]:
                maximums.append((val, pos))
        return sorted(maximums, reverse=True)
    
    def __call__(self, individual):
        possible_values = []
        
        for func, pos, height, width in zip(self.peaks_function,
                                            self.peaks_position,
                                            self.peaks_height,
                                            self.peaks_width):
            possible_values.append(func(individual, pos, height, width))
        
        if self.basis_function:
            possible_values.append(self.basis_function(individual))
        
        return max(possible_values),
    
    def changePeaks(self):
        """Order the peaks to change position, height and width."""
        for i in range(len(self.peaks_function)):
            # Change peak position
            shift = [self.random.random() - 0.5 for _ in range(len(self.peaks_position[i]))]
            shift_length = sum(s**2 for s in shift)
            shift_length = self.move_severity / math.sqrt(shift_length) if shift_length > 0 else 0
            
            shift = [shift_length * (1.0 - self.lambda_) * s \
                     + self.lambda_ * c for s, c in zip(shift, self.last_change_vector[i])]
            
            shift_length = sum(s**2 for s in shift)
            shift_length = self.move_severity / math.sqrt(shift_length) if shift_length > 0 else 0
            
            shift = [s*shift_length for s in shift]
            
            new_position = []
            final_shift = []
            for pp, s in zip(self.peaks_position[i], shift):
                new_coord = pp + s
                if new_coord < self.min_coord:
                    new_position.append(2.0 * self.min_coord - pp - s)
                    final_shift.append(-1.0 * s)
                elif new_coord > self.max_coord:
                    new_position.append(2.0 * self.max_coord - pp - s)
                    final_shift.append(-1.0 * s)
                else:
                    new_position.append(new_coord)
                    final_shift.append(s)
            
            self.peaks_position[i] = new_position
            self.last_change_vector[i] = final_shift
            
            # Change peak height
            change = self.random.gauss(0, 1) * self.height_severity
            new_value = change + self.peaks_height[i]
            if new_value < self.min_height:
                self.peaks_height[i] = 2.0 * self.min_height - self.peaks_height[i] - change
            elif new_value > self.max_height:
                self.peaks_height[i] = 2.0 * self.max_height - self.peaks_height[i] - change
            else:
                self.peaks_height[i] = new_value
            
            # Change peak width
            change = self.random.gauss(0, 1) * self.width_severity
            new_value = change + self.peaks_width[i]
            if new_value < self.min_width:
                self.peaks_width[i] = 2.0 * self.min_width - self.peaks_width[i] - change
            elif new_value > self.max_width:
                self.peaks_width[i] = 2.0 * self.max_width - self.peaks_width[i] - change
            else:
                self.peaks_width[i] = new_value

SCENARIO_1 = {"pfunc" : function1,
              "npeaks" : 5,
              "min_coord": 0.0,
              "max_coord": 100.0,
              "min_height": 30.0,
              "max_height": 70.0,
              "uniform_height": 50.0,
              "min_width": 0.0001,
              "max_width": 0.2,
              "uniform_width": 0.1,
              "lambda_": 0.0,
              "move_severity": 1.0,
              "height_severity": 7.0,
              "width_severity": 0.01}

SCENARIO_2 = {"pfunc" : cone,
              "npeaks" : 10,
              "min_coord": 0.0,
              "max_coord": 100.0,
              "min_height": 30.0,
              "max_height": 70.0,
              "uniform_height": 50.0,
              "min_width": 1.0,
              "max_width": 12.0,
              "uniform_width": 0,
              "lambda_": 0.5,
              "move_severity": 1.5,
              "height_severity": 7.0,
              "width_severity": 1.0}

SCENARIO_3 = {"pfunc" : cone,
              "npeaks" : 50,
              "min_coord": 0.0,
              "max_coord": 100.0,
              "min_height": 30.0,
              "max_height": 70.0,
              "uniform_height": 0,
              "min_width": 1.0,
              "max_width": 12.0,
              "uniform_width": 0,
              "lambda_": 0.5,
              "move_severity": 1.0,
              "height_severity": 1.0,
              "width_severity": 0.5}