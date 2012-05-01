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
# Alpha version

__author__ = "DEAP Team"
__version__ = "0.2"
__revision__ = "0.2.1"

from deap.dtm.manager import Control

_dtmObj = Control()

setOptions = _dtmObj.setOptions
start = _dtmObj.start
map = _dtmObj.map
map_async = _dtmObj.map_async
apply = _dtmObj.apply
apply_async = _dtmObj.apply_async
imap = _dtmObj.imap
imap_unordered = _dtmObj.imap_unordered
filter = _dtmObj.filter
repeat = _dtmObj.repeat
waitAll = _dtmObj.waitAll
waitAny = _dtmObj.waitAny
testAll = _dtmObj.testAll
testAny = _dtmObj.testAny
getWorkerId = _dtmObj.getWorkerId

# Control shall not be imported that way
del Control