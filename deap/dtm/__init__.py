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

# DTM : Distributed Task Manager
# Pre-alpha version

__author__ = "Marc-Andre Gardner"
__version__ = "0.2"
__revision__ = "0.2.1"

from taskmanager import DtmControl
_controller = DtmControl()

map = _controller.map
apply = _controller.apply

# DtmControl shall not be imported that way
del DtmControl
