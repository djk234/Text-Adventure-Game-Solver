# Main file to run the solver.
import solver
import gmap
import turtle




# Main method for the solver. Takes in raw input as instructions.
def main():
	instr = raw_input("Enter instructions for solver: ")
	game_map = gmap.GameMap()
	game_map.print_map()
	Tagsolver = solver.Solver(instr)
	Tagsolver.game_map = game_map
	Tagsolver.spawn_solver()



if __name__ == '__main__':
	main()