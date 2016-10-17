import subprocess
import time
import os
import signal

started = False
process0 = None

while True:
    if not started:
        print "starting..."
        started = True
        process0 = subprocess.Popen("emacs RET -batch -l dunnet", shell=True, stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
    else:
        time.sleep(2)
        process0.communicate("go east")
