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
import turtle
import Solution
import nltk
import htmlparse
import re

# Need to download pexpect here: https://pexpect.readthedocs.io/en/stable/index.html
import pexpect

engine = None

Circle_Radius = 10
Path_Length = 50

# A set of predefined commands that the solver would expect to be
# in an arbitrary text adventure game.
Commands = [
	"look",
	"go",
	"take",
	"drop",
	"put",
	"type",
	"flush",
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

Headings = [
	90,270,0,180,135,45,225,315
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

Item_Actions = []

Combination = "000"

# Main class for the solver. It will store several pieces of information, such as:
# 	1. Instructions passed in
#	2. Turtle GUI Pen, for sending GUI commands
#	3. Game Engine subproccess, spawned by pexpect
#	4. Game Map
# 	5. Item Map
# 	6. Item actions (Ie: what things you can do with items, such as dig with a shovel)
# 	7. Last command entered
#  8. Score
#  9. Dictionary of commands with possible acompanying inputs as values
#  10. All possible go directions
#  11. List of inventory items
class Solver(object):

	# Constructor function for the Solver, doesn't do much except - most initialization is
	# done when it is "spawned" as a subprocess.
	def __init__(self, instructions):
		self.instructions = instructions
		self.pen = None
		self.engine = None
		self.game_map = None
		self.item_map = None
		self.item_actions = dict()
		self.last_command = ""
		self.score = 0
		self.commands = dict()
		self.directions = Directions
		self.inventory = []
		self.other_items = [] # associated nouns with the items we have
		self.proper_nouns = []

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

	# Checks to see if this item's associated nouns can be found in this description
	def check_nouns(self, response, item):
		words = re.findall(r"[\w']+", response.lower())
		other_names = (item.name for item in self.other_items)
		for noun in item.nouns:
			# Check to see if this associated noun is one of the words  and it isn't already found
			if noun in words and noun not in other_names and noun != item.name:
				new_item = gmap.GItem(noun,self.game_map.get_current().name)
				new_item.nouns.append(item.name)
				new_item.actions = htmlparse.query_word(noun)[0]
				print new_item.actions
				new_item.parsed = True
				self.other_items.append(new_item)
				response = self.send_command("put "+item.name+" in "+noun)
				print response
				for verb in new_item.actions:
					response = self.send_command_new(verb)
					print response
					if "I don't understand" in response:
						continue
					else:
						break

	# Will take items and add them to the Solver's inventory
	def take(self, response):
		words = nltk.word_tokenize(response)
		tokens = nltk.pos_tag(words, tagset='universal')
		for (a,b) in tokens:
			if b == "NOUN":
				response = self.send_command("take "+a)
				if ("Taken." in response):
					print response
					new_item = gmap.GItem(a,self.game_map.get_current().name)
					self.inventory.append(new_item)

	# Drops all items currently in the inventory, and readds them back if possible.
	def drop(self, item):
		response = self.send_command("drop "+item.name)
		print response
		words = response.split()
		if ("Done." in words[len(words)-1]):
			response = self.send_command("take "+item.name)
			print response
		else:
			response = self.send_command("look")
			print response
			self.inventory.remove(item)
			self.take(response)

	# Sends the command and returns the response
	def send_command(self, cmd):
		self.engine.sendline(cmd)
		self.engine.expect([">"])
		return self.engine.before

	def send_command_new(self, cmd):
		self.engine.sendline(cmd)
		self.engine.expect([">",":","ftp> "])
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

	# Uses turtle GUI to draw a new room
	def draw_new_room(self, index, draw_circles, name):
		self.pen.pendown()
		self.pen.setheading(Headings[index])
		self.pen.forward(Path_Length)
		self.pen.penup()
		if draw_circles:
			self.pen.sety(self.pen.ycor()-Circle_Radius)
			self.pen.pendown()
			self.pen.pencolor("black")
			self.pen.write(name,align="center")
			self.pen.pencolor("red")
			old_heading = self.pen.heading()
			self.pen.setheading(0)
			self.pen.circle(Circle_Radius)
			self.pen.setheading(old_heading)
			self.pen.penup()
			self.pen.sety(self.pen.ycor()+Circle_Radius)
		turn = Headings[index]-180
		if (Headings[index]-180) < 0:
			turn += 360
		self.pen.setheading(turn)
		self.pen.forward(Path_Length)

	# Loops through the available directions
	def direction_loop(self):
		# Checks directions
		for i in range (len(Directions)):
			# If this direction is not already mapped in the adjacency
			if (Directions[i] not in self.game_map.get_current().adjencies and not (Directions[i] == "south" and self.game_map.get_current().name == "Old Building hallway")):
				response = self.send_command("go "+Directions[i])
				print response
				last_command = "go "+Directions[i]
				description = response[len("go "+Directions[i]):]
				# If the command resulted in you moving to a new room
				if ("You can't go that way." not in response and "You don't have a key that can open this door." not in response):
					words = response.split("\r\n")
					room_name = words[1]
					# If this new room was not already mapped in this room's adjacency
					#if (not self.game_map.check_adj_room(self.game_map.get_current(),room_name)):
					new_room = gmap.GRoom(room_name)
					new_room.set_description(description)
					new_room.insert_adjency(self.game_map.get_current(),Opp_Directions[i])
					self.game_map.get_current().insert_adjency(new_room,Directions[i])
					self.game_map.add_room(self.game_map.get_current())
					draw = self.game_map.add_room(new_room)
					self.draw_new_room(i,draw,room_name)
					response = self.send_command("go "+Opp_Directions[i])
					print(response)
					last_command = "go "+Opp_Directions[i]
					# If this new room was already mapped in this room's adjacency
					#else:
					#	self.game_map.get_current().insert_adjency(self.game_map.get_room(room_name),Directions[i])
					#	repeat_room = self.game_map.get_current().adjencies[Directions[i]]
					#	return_direction = repeat_room.get_target_room_direction(self.game_map.get_current())
					#	response = self.send_command("go "+return_direction)
					#	print(response)
					#	last_command = "go "+return_direction
					#	self.pen.setpos(self.game_map.get_current().pos[0],self.game_map.get_current().pos[1])


	# Tests if dropping items work and looks up commands for the items
	# in your inventory
	def item_loop(self):
		for item in self.inventory:
			self.drop(item)
			self.check_nouns(self.game_map.get_current().description,item)
			# Going to html parse and look at the associated verbs and nouns
			verbs = item.actions
			# if we haven't tested the verbs
			if len(item.actions) == 0 and not item.parsed:
				associated = htmlparse.query_word(item.name)
				verbs = associated[0]
				item.nouns = associated[1]
				item.parsed = True
			for verb in verbs:
				response = self.send_command(verb)
				print response
				if ("I don't understand that." not in response):
					if (verb not in item.actions):
						item.actions.append(verb)
					response = self.send_command("look")
					print response
					self.take(response)

	# Sends sequential moves to find neighboring rooms
	def sequential_command(self):
		# Initial "look" to get the name of the room (should be unnecessary)
		response = self.send_command("look")
		print(response)
		self.last_command = "look"
		self.take(response)
		self.item_loop()
		# Will loop through the directions to find neighbor rooms
		self.game_map.get_current().set_mapped()
		self.game_map.get_current().set_pos(self.pen.xcor(),self.pen.ycor())
		self.direction_loop()

	# Traverses the map and tries dropping items everywhere
	def traverse_map(self):
		self.game_map.get_current().set_pos(self.pen.xcor(),self.pen.ycor())
		self.game_map.get_current().set_mapped()
		self.game_map.get_current().traversed = True
		self.direction_loop()
		self.item_loop()
		old_room = self.game_map.get_current()
		for direction in old_room.get_directions():
			if (not self.game_map.get_current().adjencies[direction].traversed):
				response = self.send_command("go "+direction)
				self.pen.setheading(Headings[Directions.index(direction)])
				self.pen.forward(Path_Length)
				print(response)
				self.game_map.update_current(self.game_map.get_current().adjencies[direction])
				self.traverse_map()
				opp_direction = Opp_Directions[Directions.index(direction)]
				response = self.send_command("go "+opp_direction)
				self.pen.setheading(Headings[Directions.index(opp_direction)])
				self.pen.forward(Path_Length)
				self.game_map.update_current(self.game_map.get_current().adjencies[opp_direction])
				print(response)

	# Main loop for the solver to play the game
	def game_loop(self):
		self.sequential_command()
		old_room = self.game_map.get_current()
		for direction in old_room.get_directions():
			if not self.game_map.get_current().adjencies[direction].mapped:
				response = self.send_command("go "+direction)
				self.pen.setheading(Headings[Directions.index(direction)])
				self.pen.forward(Path_Length)
				print(response)
				self.game_map.update_current(self.game_map.get_current().adjencies[direction])
				self.game_loop()
				opp_direction = Opp_Directions[Directions.index(direction)]
				response = self.send_command("go "+opp_direction)
				self.pen.setheading(Headings[Directions.index(opp_direction)])
				self.pen.forward(Path_Length)
				self.game_map.update_current(self.game_map.get_current().adjencies[opp_direction])
				print(response)

	# Follows hard code instructions to win game
	def solve_game(self):
		commands = Solution.Hard_Code.split(", ")
		print(commands)
		for command in commands:
			if (len(command) > 0):
				if (command == "xxx"):
					response = self.send_command_new(Combination)
				else:
					response = self.send_command_new(command)
					if "The combination is" in response:
						print "RESPONSE ",
						print response
						Combination = response.split()[7][:3]
						print "COMBINATION ",
						print Combination
				print response

	# Performs initialization of turtle GUI
	def initialize_gui(self):
		self.pen = turtle.Turtle()
		self.pen.speed("fastest")
		self.pen.pencolor("red")
		self.pen.penup()
		self.pen.sety(self.pen.ycor()-Circle_Radius)
		self.pen.pendown()
		self.pen.circle(Circle_Radius)
		self.pen.penup()
		self.pen.sety(self.pen.ycor()+Circle_Radius)

  # Spawns the solver and game subprocess using pexpect
	# Uncomment to run normally and then comment out self.solve_game() call
	def spawn_solver(self):
		print "Starting..."
		self.initialize_gui()
		self.engine = pexpect.spawn('emacs RET -batch -l dunnet')
		self.engine.expect([">"])
		print(self.engine.before)
		self.populate_initial_commands()
		room_name = "Dead end"
		new_room = gmap.GRoom(room_name)
		new_room.set_description(self.engine.before)
		self.game_map.update_current(new_room)
		self.game_loop()
		self.game_map.print_map()
		while True:
			self.traverse_map()

		# Runs the solution solver
		#self.solve_game()

		time.sleep(10)
