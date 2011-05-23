import subprocess
import os
import sys

f = open(sys.argv[2], 'r')
workers = f.readlines()
for i,w in enumerate(workers):
    r = subprocess.call(["ssh", "-f", w, "cd "+str(os.getcwd())+" && python "+sys.argv[1]+" -f " + sys.argv[2] + " -i " + str(i)])
    assert r == 0
f.close()