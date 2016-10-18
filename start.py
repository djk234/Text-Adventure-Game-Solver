import subprocess
import time
import os
import signal

# Need to download pexpect here: https://pexpect.readthedocs.io/en/stable/index.html
import pexpect

started = False
engine = None


class Solver(object):

	def __init__(self, instructions):
		self.instructions = instructions
		self.engine = None


	def spawn_solver(self):
		while True:
    		if not started:
        		print "Starting..."
        		started = True
        		self.engine = pexpect.spawn('emacs RET -batch -l dunnet')
    		else:
        		time.sleep(2)
        		self.engine.sendline("go east")



def main():
	instr = raw_input("Enter instructions for solver: ")
	Solver = Solver(None, instr)
	Solver.spawn_solver()



if __name__ == '__main__':
	main()