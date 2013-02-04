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
import pylab

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="%prog [options] jsonfile")
    parser.add_option("-n", "--name", action="append", type="string",
        dest="stats", help=("Which statistic to plot. This argument can "
        "be specified multiple times and receive comma separated names."))
    parser.add_option("-o", "--output", action="store", type="string",
        dest="plt_file", help="Name of the file to write the figure to.")
    
    options, args = parser.parse_args(sys.argv)
    
    try:
        jfile = open(args[1], "r")
    except:
        parser.error()

    stats_dict = json.load(jfile)
    
    if options.stats:
        stats = list()
        for s_names in options.stats:
            stats.extend(s_names.split(","))
        
        for s in stats:
            pylab.plot(stats_dict[s], label=s)
    else:
        pass
    
    pylab.legend()
    
    if options.plt_file:
        pylab.savefig(options.plt_file)
    else:
        pylab.show()