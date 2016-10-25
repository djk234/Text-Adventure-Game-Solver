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
	"west",
	"northwest",
	"northeast",
	"southwest",
	"southeast"
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
		self.room_description = ""
		self.score = 0
		self.commands = dict()
		self.directions = Directions

    # Populates commands with the commands themselves and the initial possible inputs
	def populate_initial_commands(self):
		self.commands[Commands[0]] = [""]
		self.commands[Commands[1]] = Directions
		self.commands[Commands[2]] = []
		self.commands[Commands[3]] = []

	# Searches the description of the room for any possible items, we need to
	# make sure it is only taking available things (ie. read the response of the take)
	def search_possible_items(self, description):
		words = description.split()
		if ("here." in words):
			item = words[words.index("here.")-1]
			if (item not in self.commands["take"]):
				self.commands["take"].append(item)

	# Procedure that inputs a random command to the game
	def random_command(self):
		cmd1 = random.choice(self.commands.keys())
		if (len(self.commands[cmd1]) == 0):
			cmd2 = ""
		else:
			cmd2 = random.choice(self.commands[cmd1])
		print(self.commands[cmd1])
		cmd = cmd1 + " " + cmd2
		self.engine.sendline(cmd)
		self.engine.expect(cmd)
		response = self.engine.before
		if (cmd1 == "look"):
			self.search_possible_items(response)
		print(response)
		print(cmd)
		# Taking/dropping an object will add/remove that object from the inventory
		if (cmd1 == "take" and response.find("Taken.") != -1):
			self.commands["take"].remove(cmd2)
			self.commands["drop"].append(cmd2)
		elif (cmd1 == "drop" and response.find("Done.") != -1):
			self.commands["drop"].remove(cmd2)
			self.commands["take"].append(cmd2)

	# Main loop for the solver to play the game
	def game_loop(self):
		while True:
			self.random_command()
			print(self.commands)

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
