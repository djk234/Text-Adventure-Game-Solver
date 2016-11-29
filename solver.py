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

	# Will take items and add them to the Solver's inventory
	def take(self, response):
		words = nltk.word_tokenize(response)
		tokens = nltk.pos_tag(words, tagset='universal')
		for (a,b) in tokens:
			if b == "NOUN":
				response = self.send_command("take "+a)
				print response
				if ("Taken." in response):
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
		self.engine.expect([">",":"])
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
		for i in range (len(Directions)):
			if (Directions[i] not in self.game_map.get_current().adjencies):
				response = self.send_command("go "+Directions[i])
				print(response)
				last_command = "go "+Directions[i]
				description = response[len("go "+Directions[i]):]
				if ("You can't go that way." not in response and "You don't have a key that can open this door." not in response):
					words = response.split("\r\n")
					room_name = words[1]
					if (not self.game_map.check_adj_room(self.game_map.get_current(),room_name)):
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
					else:
						self.game_map.get_current().print_room()
						self.pen.setpos(self.game_map.get_current().pos[0],self.game_map.get_current().pos[1])
						response = self.send_command("go northeast")
						print(response)
						last_command = "go northeast"

	# Sends sequential moves to find neighboring rooms
	def sequential_command(self):
		# Initial "look" to get the name of the room (should be unnecessary)
		response = self.send_command("look")
		print(response)
		self.last_command = "look"
		self.take(response)
		for item in self.inventory:
			self.drop(item)
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
		for item in self.inventory:
			self.drop(item)
			# Going to html parse and look at the associated verbs
			verbs = item.actions
			# if we haven't tested the verbs
			if len(item.actions) == 0 and not item.verb_parsed:
				verbs = htmlparse.query_word(item.name)
				item.verb_parsed = True
			for verb in verbs:
				response = self.send_command(verb)
				print response
				if ("I don't understand that." not in response):
					if (verb not in item.actions):
						item.actions.append(verb)
					response = self.send_command("look")
					print response
					self.take(response)
			print item.name + ": ",item.actions
		old_room = self.game_map.get_current()
		for direction in old_room.get_directions():
			if (not self.game_map.get_current().adjencies[direction].traversed):
				print("Direction: "+direction)
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
				self.game_map.print_map()
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
					response = self.send_command(Combination)
				else:
					response = self.send_command(command)
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
		# self.solve_game()

		time.sleep(10)
