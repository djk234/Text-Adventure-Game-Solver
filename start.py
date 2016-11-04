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

Hard_Code = "get shovel, look shovel, e, e, dig, look, get cpu, look cpu, se, " \
"get food, se, look bear, drop food, look, get key, sw, get bracelet, ne, nw, " \
"nw, ne, ne, ne, e, look bins, w, w, put cpu in computer, type, toukmond, robert, " \
"ls, uncompress paper.o.Z, exit, look paper, type, ftp gamma, anonymous, toukmond, " \
"binary, send lamp.o, send shovel.o, send key.o, send  "\
"bracelet.o, send paper.o, quit, rlogin gamma, worms, get lamp, get "\
"shovel, get key, get bracelet, get paper, e, n, e, drop shovel, drop key, "\
"drop bracelet, drop paper, get weight, d, drop weight, nw, u, get "\
"statuette, look statuette, get floppy, se, d, nw, ne, drop floppy, w, s, "\
"e, turn dial clockwise, turn dial clockwise, turn dial clockwise, turn "\
"dial counterclockwise, turn dial counterclockwise, turn dial "\
"counterclockwise, w, n, e, get life, get shovel, get key, get bracelet, "\
"get paper, get floppy, d, nw, u, se, d, nw, nw, s, s, s, s, put diamond "\
"in chute, put bracelet in chute, s, get gold, e, e, s, d, look urinal, "\
"put gold in urinal, flush, n, sleep, d, sw, e, u, dig, look, get "\
"platinum, d, w, ne, u, s, put platinum in urinal, flush, n, d, sw, w, d, "\
"e, get towel, look towel, d, s, s, s, look pc, put floppy in pc, reset, , "\
"dir, type foo.txt => xxx (combination), exit, n, n, n, n, n, u, look box, "\
"put key in box, u, u, ne, ne, get axe, d, n, w, xxx (combination), cut "\
"cable, exit, get key, e, n, get lamp, get license, get silver, w, put "\
"silver in mail, n, n, e, e, e, e, e, get coins, get egg (in rooms 60 to "\
"78), w, w, w, w, w, s, s, put egg in mail, put coins in mail, n, n, n, n, "\
"e, e, e, e, e, look bus, in, s, s, s, w, w, w, w, w, nw, out, n, get "\
"bone, e, e, get nitric, press switch, n, get glycerine, w, look bone, get "\
"jar, get ruby, s, w, s, in, se, out, e, e, e, e, n, n, put nitric in jar, "\
"put glycerine in jar, drop jar, in, n, n, put ruby in disposal, d, get "\
"amethyst, u, put amethyst in disposal, d, ne, sw, u, u, w, w, s, w, s, "\
"se, s, e, s, w, type, rlogin endgame, drop license, drop bone, drop key, "\
"get diamond, get gold, get platinum, get amethyst, n, n, n, n, get bill, "\
"n, get mona, s, drop bill, drop mona, drop diamond, drop gold, drop "\
"platinum, drop amethyst, s, s, s, s, get silver, get egg, get coins, get "\
"ruby, get bracelet, n, n, n, n, n, drop silver, drop egg, drop coins, "\
"drop ruby, drop bracelet, n, look"\

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
		words = response.split()
		for word in words:
			response = self.send_command("take "+word)
			print response
			if ("Taken." in response):
				new_item = gmap.GItem(word,self.game_map.get_current().name)
				self.inventory.append(new_item)

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
				if ("You can't go that way." not in response and "You don't have a key that can open this door." not in response):
					words = response.split("\r\n")
					room_name = words[1]
					if (not self.game_map.check_adj_room(self.game_map.get_current(),room_name)):
						new_room = gmap.GRoom(room_name)
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
				self.game_map.print_map()
				opp_direction = Opp_Directions[Directions.index(direction)]
				response = self.send_command("go "+opp_direction)
				self.pen.setheading(Headings[Directions.index(opp_direction)])
				self.pen.forward(Path_Length)
				self.game_map.update_current(self.game_map.get_current().adjencies[opp_direction])
				print(response)

	# Follows hard code instructions to win game
	def solve_game(self):
		commands = Hard_Code.split(", ")
		print(commands)
		for command in commands:
			if (len(command) > 0):
				response = self.send_command(command)
				print response


    # Spawns the solver and game subprocess using pexpect
	# Uncomment to run normally and then comment out self.solve_game() call
	def spawn_solver(self):
		print "Starting..."
		#self.pen = turtle.Turtle()
		self.engine = pexpect.spawn('emacs RET -batch -l dunnet')
		self.engine.expect([">",":"])
		print(self.engine.before)
		# self.pen.speed("fastest")
		#self.pen.pencolor("red")
		#self.pen.penup()
		#self.pen.sety(self.pen.ycor()-Circle_Radius)
		#self.pen.pendown()
		#self.pen.circle(Circle_Radius)
		#self.pen.penup()
		#self.pen.sety(self.pen.ycor()+Circle_Radius)
		#self.populate_initial_commands()
		room_name = "Dead end"
		new_room = gmap.GRoom(room_name)
		self.game_map.update_current(new_room)
		#self.game_loop()
		#self.game_map.print_map()
		#while True:
			#self.traverse_map()
		self.solve_game()
		time.sleep(10)

# Uncomment inner to run normally
def main():
	instr = raw_input("Enter instructions for solver: ")
	# wn = turtle.Screen()
	game_map = gmap.GameMap()
	game_map.print_map()
	Tagsolver = Solver(instr)
	Tagsolver.game_map = game_map
	Tagsolver.spawn_solver()



if __name__ == '__main__':
	main()
