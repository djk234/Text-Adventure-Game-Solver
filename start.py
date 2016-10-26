# Main file for the solver.
# Authors:
# Will Ronchetti wrr33@cornell.edu
# David Karabinos djk234@cornell.edu


import subprocess
import time
import os
import signal
import random
import gmap


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

Opp_Directions = [
	"south",
	"north",
	"west",
	"east",
	"southeast",
	"southwest",
	"northeast",
	"northwest"
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
		self.last_command = ""
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
		if ("here." in words and "There is " in description):
			item = words[words.index("here.")-1]
			if (item not in self.commands["take"]):
				self.commands["take"].append(item)

	# Will remove items from the command list based on response
	# Taking/dropping an object will add/remove that object from the inventory
	def take_drop(self, response):
		if (self.last_command.find("take") != -1 and response.find("Taken.") != -1):
			direct_obj = self.last_command.split("take ")
			if (len(direct_obj) > 1):
				direct_obj = direct_obj[1]
			else:
				direct_obj = direct_obj[0]
			print(direct_obj)
			self.commands["take"].remove(direct_obj)
			self.commands["drop"].append(direct_obj)
		elif (self.last_command.find("drop") != -1 and response.find("Done.") != -1):
			direct_obj = self.last_command.split("drop ")
			if (len(direct_obj) > 1):
				direct_obj = direct_obj[1]
			else:
				direct_obj = direct_obj[0]
			self.commands["drop"].remove(direct_obj)
			self.commands["take"].append(direct_obj)

	# Sends the command and returns the response
	def send_command(self, cmd):
		self.engine.sendline(cmd)
		self.engine.expect(">"+cmd)
		return self.engine.before

	# Procedure that inputs a random command to the game
	def random_command(self):
		cmd1 = random.choice(self.commands.keys())
		if (len(self.commands[cmd1]) == 0):
			cmd2 = ""
		else:
			cmd2 = random.choice(self.commands[cmd1])
		cmd = cmd1 + " " + cmd2
		self.engine.sendline(cmd)
		self.engine.expect(">"+cmd)
		response = self.engine.before
		if (self.last_command.find("look") != -1):
			self.search_possible_items(response)
		print(response)
		print(cmd)
		self.take_drop(response)
		self.last_command = cmd

	# Loops through the available directions
	def direction_loop(self):
		for direction in Directions:
			response = self.send_command("go "+direction)

	# Sends sequential moves to find neighboring rooms
	def sequential_command(self):
		# Initial "look" to get the name of the room (should be unnecessary)
		response = self.send_command("look")
		print(response)
		print("look")
		room_name = response.split("\n")[1]
		new_room = gmap.GRoom(room_name)
		self.last_command = "look"
		self.game_map.update_current(new_room)
		# Will loop through the directions to find neighbor rooms
		# self.direction_loop()

	# Main loop for the solver to play the game
	def game_loop(self):
		while True:
			time.sleep(1)
			self.sequential_command()
			# print(self.commands)

    # Spawns the solver and game subprocess using pexpect
	def spawn_solver(self):
		print "Starting..."
		self.engine = pexpect.spawn('emacs RET -batch -l dunnet')
		self.populate_initial_commands()
		self.game_loop()


def main():
	instr = raw_input("Enter instructions for solver: ")
	game_map = gmap.GameMap()
	game_map.print_map()
	Tagsolver = Solver(instr)
	Tagsolver.game_map = game_map
	Tagsolver.spawn_solver()



if __name__ == '__main__':
	main()
