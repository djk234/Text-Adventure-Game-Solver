# File for the map class
# Authors:
# Will Ronchetti wrr33@cornell.edu
# David Karabinos djk234@cornell.edu

# Item class - holds the ID and current location. Can be in inventory.
class GItem(object):

	def __init__(self, ID, location):
		self.name = ID
		self.location = location
		self.redeemed = False
		self.actions = []

	# Returns redeem status of item
	def is_redeemed(self):
		return self.redeemed

	# Sets an item as redeemed, and updates the items location to the treasure room
	def redeem(self, location):
		self.redeemed = True
		self.location = location

	# Attempts an action associated with an item. If it succeeds, add the (item,action)
	# pair to the item action dictionary
	def try_action(self, action):
		response = self.send_command(action)
		if "don't understand" in response:
			print(action + " not possible.")
			return
		else:
			print(action + " suceeded!")
			self.insert_item_action(item, action)

	# Inserts a new item/action pair into the item action dictionary
	def insert_item_action(self):
		self.item_actions[item] = action

	# Performs the action associated with an item
	def perform_item_action(self):
		self.send_command(self.item_actions[item])

	# Performs all item actions
	def do_all_actions(self):
		for action in self.item_actions.itervalues():
			self.send_command(action)

# Class for room. Contains the room ID, a hashmap of tuples
# (direction,room) of possible go commands, the items currently in the room
# and items that belong in this room to increase the score.
class GRoom(object):

	def __init__(self, name, local_items = None, treasure_items = None):
		self.name = name
		self.adjencies = dict()
		self.items = []
		self.mapped = False
		self.traversed = False
		self.description = ""
		self.pos = []

	# Procedure that adds a new adjency edge to the room
	def insert_adjency(self, new_room, direction):
		self.adjencies[direction] = new_room

	# Sets the description for this room
	def set_description(self, description):
		self.description = description

	# Returns a list of the directions that can be moved to from the current room.
	# Since self.adjencies is a hashmap, and we use the direcitons as keys, we can
	# simply return a list of the keys in the hashmap.
	def get_directions(self):
		return self.adjencies.keys()

	# Appends item to the items currently in the room, indicating that an items current
	# location is in room self.
	def insert_item(self, item):
		self.items.append(item)

	# Indicates that a room has been mapped and should not be mapped again.
	def set_mapped(self):
		self.mapped = True

    # Returns a list of items currently in the room.
	def get_items(self):
		return self.items

	# Sets the room's position
	def set_pos(self,x,y):
		self.pos = [x,y]

	# Easy informative and infoto read print of the room
	def print_room(self):
		print(self.name)
		directions = self.get_directions()
		for direction in directions:
			print(direction+": "+self.adjencies[direction].name)
		print(self.items)
		print(self.mapped)
		print(self.pos)
		print("")

	# Sets room description
	def set_description(self, description):
		# Split on newline, which should dilineate the command from
		# the description.
		cmd_index = description.find("\n")
		self.description = description[cmd_index:]


# Class for the Game Map. The Map itself is constructed by the solver
# as it navigates through the game, producing an adjency matrix. The edges
# of the matrix have identifiers indicating the direction needed to traverse
# into the room - this identifier is stored in the room class, since direction
# is relative to the current room
#
# 					east->		   east->
# 			room1 <------> room2 <------> room3
# 			  |								|
# 			  | 							|	north
# 			  |		east->			east->	|
#			room4 <-----> room5 <---------->
#
class GameMap(object):

	def __init__(self):
		self.current_room = None
		self.room_list = []

	# Returns true if the room has been discovered
	def check_room(self, room_name):
		names = [room.name for room in self.room_list]
		return room_name in names

	# Checks if this room is in the adjacency
	def check_adj_room(self, room, adj_room_name):
		for direction in room.adjencies:
			if (room.adjencies[direction].name == adj_room_name):
				return True
		return False

	# Returns the room with that room name, returns None otherwise
	def get_room(self, room_name):
		names = [room.name for room in self.room_list]
		if (room_name in names):
			index = names.index(room_name)
			if (index != -1):
				return self.room_list[index]
			else:
				return None
				
	# Updates current room to room
	def update_current(self, new_room):
		self.current_room = new_room
		self.add_room(new_room)

	# Adds new room to the list without updating current, or updates the room with new adjencies
	def add_room(self, new_room):
		names = [room.name for room in self.room_list]
		if (new_room.name not in names):
			self.room_list.append(new_room)
			return True
		else:
			self.room_list[names.index(new_room.name)] = new_room
			return False

	# Returns the current room
	def get_current(self):
		return self.current_room

	# Prints all of the room information for all of the rooms on the map
	def print_map(self):
		print("Rooms:")
		for room in self.room_list:
			room.print_room()
