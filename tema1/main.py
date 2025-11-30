import sys
from SolveContext import SolveContext
from AstarSolveStrategy import AstarSolveStrategy
from utils import read_yaml_file
import time
import check_constraints

if __name__ == "__main__":
    start = time.perf_counter()
    strategy = sys.argv[1]
    input_file = sys.argv[2]

    solve_context = None
    if strategy == "astar":
        solve_context = SolveContext(AstarSolveStrategy())
    
    input = read_yaml_file(input_file)
    res = solve_context.perform_solve(input)
    print(res)
    end = time.perf_counter()
    print(f"Elapsed: {end - start:.6f} s")

    timetable = res

    constangerii_incalcate, materii_neacoperite = check_constraints.check_mandatory_constraints(timetable, input)
    print(f'Constrangeri incalcate: {constangerii_incalcate}, Materii neacoperite: {materii_neacoperite}')
    constangerii_incalcate = check_constraints.check_optional_constraints(timetable, input)
    print(f'Constrangeri optionale incalcate: {constangerii_incalcate}')

    # print(utils.pretty_print_timetable(timetable, input_file))