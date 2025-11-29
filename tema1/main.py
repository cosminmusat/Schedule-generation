import sys
from SolveContext import SolveContext
from AstarSolveStrategy import AstarSolveStrategy
from utils import read_yaml_file

if __name__ == "__main__":
    strategy = sys.argv[1]
    input_file = sys.argv[2]

    # solve_context = None
    # if strategy == "astar":
    #     solve_context = SolveContext(AstarSolveStrategy())
    
    input = read_yaml_file(input_file)
    # solve_context.perform_solve(input)

    # timetable =  {'Luni': {(8, 10): {'EG390': None}}}
    timetable = {'Luni': {(8, 10): {'EG324': None, 'EG390': ('Andreea Dinu', 'DS')}}}

    astar = AstarSolveStrategy()
    astar.solve(input)

    print(astar.get_neighbours(timetable))