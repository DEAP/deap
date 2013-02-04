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
DTM version of the sssched utility by Devert and Gagne
(http://marmakoide.org/content/code/sssched.html)

Execute concurrently a list of independant tasks
specified in a file passed with the -c command line option.
"""


import subprocess
import time
import sys
import optparse
import logging


from deap import dtm

_logger = logging.getLogger("dtm.sssched")

def executor(taskCmd):
    _logger.info("Lauching %s on worker %s", taskCmd, dtm.getWorkerId())
    return subprocess.call(taskCmd, stdout=sys.stdout, stderr=sys.stderr)

def main(fTasks):
    tasksList = []
    with open(fTasks) as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                tasksList.append(line)
    
    retVals = dtm.map(executor, tasksList)
    if sum(retVals) > 0:
        _logger.warning("Some tasks did not run well (return code > 0) :")
        for i in range(len(retVals)):
            if retVals[i] > 0:
                _logger.warning("%s returns %s", tasksList[i], retVals[i])
    
    _logger.info("Done")

if __name__ == '__main__':
    cmdLine = optparse.OptionParser(description = "Simple script scheduler (sssched) for remote job management")
    cmdLine.add_option("-c", "--commands", 
                        dest = "commandsFileName",
                        action = "store",
                        help = "File with list of commands to perform (default:\"commands.lst\")",
                        type = "string")
    
    (options, args) = cmdLine.parse_args()
    dtm.start(main, options.commandsFileName)