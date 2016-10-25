# Main file for the solver.
# Authors:
# Will Ronchetti wrr33@cornell.edu
# David Karabinos djk234@cornell.edu


import subprocess
import time
import os
import signal
import random


# Need to download pexpect here: https://pexpect.readthedocs.io/en/stable/index.html
import pexpect

engine = None

# A set of predefined commands that the solver would expect to be
# in an arbitrary text adventure game.
Commands = [
	"look",
	"go",
	"take",
	"drop",
	"score"
]

# A set of predefined directions that would be expected in a game.
Directions = [
	"north",
	"south",
	"east",
	"west"
]


# Main class for the solver. It will store several pieces of information, such as:
# 	1. Instructions passed in
#	2. Game engine instance to be communicated with
#	3. Game map
#	4. Item map
# 	5. Current score
# 	6. Commands
# 	7. Directions
#  ... anything else we need as we go.
class Solver(object):

	def __init__(self, instructions):
		self.instructions = instructions
		self.engine = None
		self.game_map = None
		self.item_map = None
		self.score = 0
		self.commands = dict()
		self.directions = Directions

    # Populates commands with the commands themselves and the initial possible inputs
	def populate_initial_commands(self):
		self.commands[Commands[0]] = [""]
		self.commands[Commands[1]] = Directions
		self.commands[Commands[2]] = [""]
		self.commands[Commands[3]] = [""]

	# Procedure that inputs a random command to the game
	def random_command(self):
		cmd1 = random.choice(self.commands.keys())
		cmd2 = random.choice(self.commands[cmd1])
		cmd = cmd1 + " " + cmd2
		self.engine.sendline(cmd)
		self.engine.expect(cmd)
		print(self.engine.before)
		print(cmd)

	# Main loop for the solver to play the game
	def game_loop(self):
		while True:
			self.random_command()

    # Spawns the solver and game subprocess using pexpect
	def spawn_solver(self):
		print "Starting..."
		self.engine = pexpect.spawn('emacs RET -batch -l dunnet')
		self.populate_initial_commands()
		self.game_loop()


def main():
	instr = raw_input("Enter instructions for solver: ")
	Tagsolver = Solver(instr)
	Tagsolver.spawn_solver()



if __name__ == '__main__':
	main()
