# Call with python main.py [n_pages] [symptoms.json]

import subprocess
import sys
import time

N = int(sys.argv[1])
t = time.time()
if len(sys.argv) < 3:
    # initialize symptoms.json
    subprocess.call(["python", "pagerank.py", "4"])
    N -= 4

while N > 0:
    errored = False
    if N < 52:
        try:
            subprocess.check_call(["python", "pagerank.py", str(N), "symptoms.json"])
        except:
            errored = True

        # only consider it a success if it did not error out
        if not errored:
            N -= N
    else:
        try:
            subprocess.check_call(["python", "pagerank.py", "52", "symptoms.json"])
        except:
            errored = True

        # only consider it success if it did not error out
        if not errored:
            N -= 52

print 'TOTAL PROCESS TOOK:', time.time() - t, 'seconds'
