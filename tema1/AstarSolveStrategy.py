from itertools import count
import json
from SolveStrategy import SolveStrategy
from heapq import heappop, heappush
import utils
import check_constraints
import copy

Timetable = dict[str, dict[tuple[int, int], dict[str, tuple[str, str]]]]

class AstarSolveStrategy(SolveStrategy):
    def __init__(self):
        self.timetable: Timetable = {}

    def solve(self, input: dict):
        self.input = input
        self.days = input[utils.ZILE]
        self.intervals = list(map(eval, input[utils.INTERVALE]))
        self.subjects = list(input[utils.MATERII].keys())
        self.profs = list(input[utils.PROFESORI].keys())
        self.rooms = list(input[utils.SALI].keys())
        self.no_nodes_generated = 0
        # res = self.astar(self.timetable, self.h)
        res = self.beam_search(self.timetable, 30, self.h, 1000000)
        print(f'Numar noduri generate: {self.no_nodes_generated}')
        return res
        # A* algorithm implementation

    def get_next_entry(self, node: Timetable):
        """
        Returns the next day, interval, room tuple to fill in the timetable.
        """
        day_idx = -1
        days_node = list(node.keys())
        for i, day in enumerate(self.days):
            if day not in days_node:
                break
            day_idx = i
        interval_idx = -1
        intervals_day_node = list(node.get(self.days[day_idx], {}).keys())
        for i, interval in enumerate(self.intervals):
            if interval not in intervals_day_node:
                break
            interval_idx = i
        room_idx = -1
        rooms_interval_node = list(node.get(self.days[day_idx], {}).get(self.intervals[interval_idx], {}).keys())
        for i, room in enumerate(self.rooms):
            if room not in rooms_interval_node:
                break
            room_idx = i
        
        if day_idx == -1 and interval_idx == -1 and room_idx == -1:
            day_idx = interval_idx = room_idx = 0
        else:
            room_idx += 1
            if room_idx == len(self.rooms):
                room_idx = 0
                interval_idx += 1
                if interval_idx == len(self.intervals):
                    interval_idx = 0
                    day_idx += 1

        return day_idx, interval_idx, room_idx

    def get_remaining_steps(self, node: Timetable) -> int:
        day_idx, interval_idx, room_idx = self.get_next_entry(node)
        
        if day_idx == len(self.days):
            return 0
        else:
            total_steps = len(self.days) * len(self.intervals) * len(self.rooms)
            current_step = day_idx * len(self.intervals) * len(self.rooms) + interval_idx * len(self.rooms) + room_idx
            return total_steps - current_step

    def is_final(self, node: Timetable):        
        remaining_steps = self.get_remaining_steps(node)

        constrangeri_incalcate, materii_neacoperite = check_constraints.check_mandatory_constraints(node, self.input)
        return constrangeri_incalcate == 0 and materii_neacoperite == 0 and remaining_steps == 0
    
    def check_student_allocation(self, node: Timetable):
        student_allocation = {}
        expected_allocation = self.input[utils.MATERII]
        reamining_prof_intervals = {}
        remaining_room_slots = {}
        rooms_data = self.input[utils.SALI]
        for subject in self.subjects:
            student_allocation[subject] = 0

        for prof in self.profs:
            reamining_prof_intervals[prof] = 0

        for room in self.rooms:
            remaining_room_slots[room] = 0
        
        for day in node.keys():
            for interval in node[day].keys():
                for room in node[day][interval].keys():
                    if node[day][interval][room]:
                        prof, subject = node[day][interval][room]
                        student_allocation[subject] += rooms_data[room]['Capacitate']
                        reamining_prof_intervals[prof] += 1

        for prof in self.profs:
            reamining_prof_intervals[prof] = 7 - reamining_prof_intervals[prof]
        
        total_steps = len(self.days) * len(self.intervals) * len(self.rooms)
        day_idx, interval_idx, room_idx = self.get_next_entry(node)
        current_step = day_idx * len(self.intervals) * len(self.rooms) + interval_idx * len(self.rooms) + room_idx
        for i in range(current_step, total_steps):
            remaining_room_slots[self.rooms[i % len(self.rooms)]] += 1

        for subject in self.subjects:

            remaining_students = expected_allocation[subject] - student_allocation[subject]

            while remaining_students > 0:

                eligible_profs = [prof for prof in self.profs if subject in self.input[utils.PROFESORI][prof][utils.MATERII] and reamining_prof_intervals[prof] > 0]
                eligible_rooms = [room for room in self.rooms if remaining_room_slots[room] > 0 and subject in self.input[utils.SALI][room][utils.MATERII]]

                if not eligible_profs or not eligible_rooms:
                    return False
                prof = min(eligible_profs, key=lambda p: len(self.input[utils.PROFESORI][p][utils.MATERII]))
                room = min(eligible_rooms, key=lambda r: self.input[utils.SALI][r]['Capacitate'])
                reamining_prof_intervals[prof] -= 1
                remaining_room_slots[room] -= 1
                student_allocation[subject] += self.input[utils.SALI][room]['Capacitate']
                remaining_students -= self.input[utils.SALI][room]['Capacitate']

        for subject in self.subjects:
            if student_allocation[subject] < expected_allocation[subject]:
                return False
            
        return True                        
    
    def h(self, node: Timetable):        
        remaining_steps = self.get_remaining_steps(node)
        
        constrangeri_incalcate, materii_neacoperite = check_constraints.check_mandatory_constraints(node, self.input)
        constrangeri_opt_incalcate = check_constraints.check_optional_constraints(node, self.input)
        return remaining_steps + constrangeri_incalcate + materii_neacoperite + 2 * constrangeri_opt_incalcate

    def get_neighbours(self, node: Timetable):
        neighbours = []
        # Generate neighbours logic
        day_idx, interval_idx, room_idx = self.get_next_entry(node)

        if day_idx == len(self.days):
            return []

        node_copy = copy.deepcopy(node)

        node_copy.setdefault(self.days[day_idx], {}).setdefault(self.intervals[interval_idx], {})

        empty_room_case_added = False
        for prof in self.profs:
            for subject in self.subjects:

                new_node = node_copy
                new_node[self.days[day_idx]][self.intervals[interval_idx]][self.rooms[room_idx]] = (prof, subject)

                if check_constraints.check_mandatory_constraints(new_node, self.input)[0] > 0:
                    if not empty_room_case_added:
                        new_node[self.days[day_idx]][self.intervals[interval_idx]][self.rooms[room_idx]] = None
                        empty_room_case_added = True
                    else:
                        continue
                if not self.check_student_allocation(new_node):
                    continue

                neighbours.append(copy.deepcopy(new_node))
        return neighbours
    
    def node_key(self, node: Timetable) -> str:
        def convert(o):
            if isinstance(o, dict):
                # sort by key's string repr to have deterministic order
                return {str(k): convert(v) for k, v in sorted(o.items(), key=lambda x: str(x[0]))}
            if isinstance(o, tuple):
                return list(o)
            return o
        return json.dumps(convert(node), sort_keys=True, ensure_ascii=False)

    def astar(self, start, h):
        # Frontiera, ca listă (heap) de tupluri (cost_f, nod)
        frontier = []
        counter = count()
        heappush(frontier, (0 + h(start), next(counter), start))
        open_set = set([self.node_key(start)])  # Nodurile din frontiera

        # Nodurile descoperite ca dicționar nod -> (părinte, cost_g-până-la-nod)
        discovered = {self.node_key(start): (None, 0)}

        end = None
        # Implementăm algoritmul A*
        while frontier:
            _, _, current_node = heappop(frontier)
            print(self.get_remaining_steps(current_node))
            if self.is_final(current_node):
                end = current_node
                break
            open_set.remove(self.node_key(current_node))
            neighbours_ = self.get_neighbours(current_node)
            self.no_nodes_generated += len(neighbours_)
            for neighbor in neighbours_:
                tentative_cost_g = discovered[self.node_key(current_node)][1] + 1  # presupunem costul 1 pentru fiecare pas
                cost_g_neighbor = discovered[self.node_key(neighbor)][1] if self.node_key(neighbor) in discovered else float('inf')
                if tentative_cost_g < cost_g_neighbor:
                    discovered[self.node_key(neighbor)] = (current_node, tentative_cost_g)
                    cost_f = tentative_cost_g + h(neighbor)
                    if self.node_key(neighbor) not in open_set:
                        open_set.add(self.node_key(neighbor))
                        heappush(frontier, (cost_f, next(counter), neighbor))
        return end

    def beam_search(self, start, B, h, limita):
        beam = [start]
        visited = [start]

        counter = count()

        end = None

        while len(beam) > 0 and len(visited) < limita:
            succ = []
            for node in beam:
                if self.is_final(node):
                    end = node
                    break
                neighbors = self.get_neighbours(node)
                for neighbor in neighbors:
                    heappush(succ, (h(neighbor), next(counter), neighbor))
            
            selected = [f for _, _, f in succ[:B]]
            visited += selected
            beam = selected

        return end