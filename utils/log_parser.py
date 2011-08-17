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

import json
# this shall be changed for argparse (Python 2.7+)
import optparse
import re
import sys

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="%prog [options] logfile")
    parser.add_option("-o", "--output", action="store", type="string",
        dest="outfile", help="Write output to OUTFILE in JSON format.")
    parser.add_option("-t", "--transpose", action="store_true",
        dest="transpose", help=("Transpose the statistics values. Each entry "
        "in the list of a statistic is a tuple containing all objectives for "
        "the iteration. When transposed, the list will instead contain "
        "N lists, where N is the number of objectives, and those lists "
        "will be containt the value for each iteration."))
    
    options, args = parser.parse_args(sys.argv)
    
    try:
        logfile = open(args[1], "r")
    except IndexError:
        logfile = sys.stdin
    except:
        parser.error()
    
    # First line is the columns' name
    col_names = logfile.readline().split()
    log = dict([(token, list()) for token in col_names])
    
    split_re = "[^\[^\]^\s]+|\[[^\[^\]]+\]"
    for line in logfile:
        line_values = re.findall(split_re, line)
        for value, name in zip(line_values, col_names):
            try:
                log[name].append(eval(value))
            except SyntaxError:
                log[name].append(value)
    
    if options.transpose:
        for key, value in log.items():
            try:
                log[key] = zip(*value)
            except TypeError:
                pass
    
    if options.outfile:
        json.dump(log, open(options.outfile, "w"))
    else:
        print log