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
		self.pen = None
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
		self.engine.expect(">")
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
			self.pen.circle(Circle_Radius)
			self.pen.penup()
			self.pen.sety(self.pen.ycor()+Circle_Radius)
		self.pen.setheading(Headings[index]-180)
		self.pen.forward(Path_Length)

	# Loops through the available directions
	def direction_loop(self):
		for i in range (len(Directions)):
			time.sleep(1)
			response = self.send_command("go "+Directions[i])
			print(response)
			last_command = "go "+Directions[i]
			if ("You can't go that way." not in response):
				words = response.split("\r\n")
				room_name = words[1]
				new_room = gmap.GRoom(room_name)
				new_room.insert_adjency(self.game_map.get_current(),Opp_Directions[i])
				self.game_map.get_current().insert_adjency(new_room,Directions[i])
				self.game_map.add_room(self.game_map.get_current())
				draw = self.game_map.add_room(new_room)
				self.draw_new_room(i,draw,room_name)
				response = self.send_command("go "+Opp_Directions[i])
				print(response)
				last_command = "go "+Opp_Directions[i]

	# Sends sequential moves to find neighboring rooms
	def sequential_command(self):
		# Initial "look" to get the name of the room (should be unnecessary)
		response = self.send_command("look")
		print(response)
		room_name = response.split("\r\n")[1]
		new_room = gmap.GRoom(room_name)
		self.last_command = "look"
		self.game_map.update_current(new_room)
		# Will loop through the directions to find neighbor rooms
		self.direction_loop()
		self.game_map.get_current().set_mapped()

	# Main loop for the solver to play the game
	def game_loop(self):
		self.sequential_command()
		self.game_map.print_map()
		for direction in self.game_map.get_current().get_directions():
			response = self.send_command("go "+direction)
			self.pen.setheading(Headings[Directions.index(direction)])
			self.pen.forward(Path_Length)
			print(response)
			self.game_map.update_current(self.game_map.get_current().adjencies[direction])
			print "Current: ",
			print self.game_map.get_current().name
			self.sequential_command()
			self.game_map.print_map()
			opp_direction = Opp_Directions[Directions.index(direction)]
			response = self.send_command("go "+opp_direction)
			self.pen.setheading(Headings[Directions.index(opp_direction)])
			self.pen.forward(Path_Length)
			self.game_map.update_current(self.game_map.get_current().adjencies[opp_direction])
			print "Current: ",
			print self.game_map.get_current().name
			print(response)

    # Spawns the solver and game subprocess using pexpect
	def spawn_solver(self):
		print "Starting..."
		self.pen = turtle.Turtle()
		self.engine = pexpect.spawn('emacs RET -batch -l dunnet')
		self.engine.expect(">")
		print(self.engine.before)
		self.pen.pencolor("red")
		self.pen.penup()
		self.pen.sety(self.pen.ycor()-Circle_Radius)
		self.pen.pendown()
		self.pen.circle(Circle_Radius)
		self.pen.penup()
		self.pen.sety(self.pen.ycor()+Circle_Radius)
		self.populate_initial_commands()
		self.game_loop()
		time.sleep(10)


def main():
	instr = raw_input("Enter instructions for solver: ")
	wn = turtle.Screen()
	game_map = gmap.GameMap()
	game_map.print_map()
	Tagsolver = Solver(instr)
	Tagsolver.game_map = game_map
	Tagsolver.spawn_solver()



if __name__ == '__main__':
	main()
