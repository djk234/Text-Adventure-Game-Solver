import subprocess
import time
import os
import signal

started = False

while True:
    if not started:
        print "starting..."
        started = True
        process0 = subprocess.Popen("emacs RET -batch -l dunnet", shell=True, stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
    else:
        time.sleep(2)
        subprocess.Popen("go east",shell=True)
