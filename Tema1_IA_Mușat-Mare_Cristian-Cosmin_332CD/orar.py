import sys
from csp import PCSP
from astar import ASTAR
from utils import pretty_print_timetable
from check_constraints import *
import os

if __name__ == "__main__":
    algorithm = sys.argv[1]
    case = sys.argv[2]
    if algorithm == "astar":
        astar = ASTAR(case)
        sol = astar.solve()
        file_name = case.split("/")[-1].split(".")[0]
        if not os.path.exists("Cristian-Cosmin_Musat-Mare_results"):
            os.makedirs("Cristian-Cosmin_Musat-Mare_results")
        with open(f"Cristian-Cosmin_Musat-Mare_results/{file_name}.txt", "w") as f:
            f.write(pretty_print_timetable(sol.schedule, case))
        