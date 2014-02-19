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
DEAP (Distributed Evolutionary Algorithms in Python) is a novel 
evolutionary computation framework for rapid prototyping and testing of 
ideas. Its design departs from most other existing frameworks in that it 
seeks to make algorithms explicit and data structures transparent, as 
opposed to the more common black box type of frameworks. It also 
incorporates easy parallelism where users need not concern themselves with 
gory implementation details like synchronization and load balancing, only 
functional decomposition.

The five founding hypotheses of DEAP are:

(1) The user knows best. Users should be able to understand the internal 
    mechanisms of the framework so that they can extend them easily to better 
    suit their specific needs.

(2) User needs in terms of algorithms and operators are so vast that it would 
    be unrealistic to think of implementing them all in a single framework. 
    However, it should be possible to build basic tools and generic mechanisms 
    that enable easy user implementation of most any EA variant.

(3) Speedy prototyping of ideas is often more precious than speedy execution 
    of programs. Moreover, code compactness and clarity is also very precious.

(4) Even though interpreted, Python is fast enough to execute EAs. Whenever 
    execution time becomes critical, compute intensive components can always 
    be recoded in C. Many efficient numerical libraries are already available 
    through Python APIs.

(5) Easy parallelism can alleviate slow execution.

And these hypotheses lead to the following objectives:

**Rapid prototyping**
    Provide an environment allowing users to quickly implement their own 
    algorithms without compromise.

**Parallelization made easy**
   Allow for straightforward parallelization; users should not be forced to 
   specify more than the granularity level of their functional decomposition.

**Adaptive load balancing**
    The workload should automatically and dynamically be distributed among 
    available compute units; user intervention should be optional and limited 
    to hints of relative loads of tasks.

**Preach by examples**
    Although the aim of the framework is not to provide ready made solutions, 
    it should nevertheless come with a substantial set of real-world examples 
    to guide the apprenticeship of users.
"""

__author__ = "DEAP Team"
__version__ = "0.9"
__revision__ = "0.9.2"
