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

	# Returns redeem status of item
	def is_redeemed(self):
		return self.redeemed

	# Sets an item as redeemed, and updates the items location to the treasure room
	def redeem(self, location):
		self.redeemed = True
		self.location = location

# Class for room. Contains the room ID, a hashmap of tuples
# (direction,room) of possible go commands, the items currently in the room
# and items that belong in this room to increase the score.
class GRoom(object):

	def __init__(self, name, adjencies=None, local_items = None, treasure_items = None):
		self.name = name
		self.adjencies = adjencies
		self.local_items = local_items
		self.treasure_items = treasure_items

	# Procedure that adds a new adjency edge to the room
	def insert_adjency(self, new_room, direction):
		self.adjencies[direction] = new_room

	# Returns a list of the directions that can be moved to from the current room.
	# Since self.adjencies is a hashmap, and we use the direcitons as keys, we can
	# simply return a list of the keys in the hashmap.
	def get_directions(self):
		return self.adjencies.keys()

	# Appends item to the items currently in the room, indicating that an items current
	# location is in room self.
	def insert_item(self, item):
		self.local_items.append(item)

    # Returns a list of items currently in the room.
	def get_items(self):
		return self.local_items

	# Done if the item has been dropped in the correct treasure room, and updates
	# the room object to indicate so.
	def insert_treasure_iteim(self, item):
		self.treasure_items.append(item)

	# Easy informative and infoto read print of the room
	def print_room(self):
		print(self.name)
		print(self.adjencies)
		print(self.local_items)


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

	# Updates current room to room
	def update_current(self, new_room):
		self.current_room = new_room
		names = [room.name for room in self.room_list]
		if (new_room.name not in names):
			self.room_list.append(new_room)

	# Returns the current room
	def get_current(self):
		return self.current_room

	# Prints all of the room information for all of the rooms on the map
	def print_map(self):
		print("Rooms:")
		for room in self.room_list:
			room.print_room()
