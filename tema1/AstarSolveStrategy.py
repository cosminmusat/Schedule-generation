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
        return self.astar(self.timetable, self.h)
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


    def is_final(self, node: Timetable):
        day_idx, interval_idx, room_idx = self.get_next_entry(node)
        
        if day_idx == len(self.days):
            remaining_steps = 0
        else:
            total_steps = len(self.days) * len(self.intervals) * len(self.rooms)
            current_step = day_idx * len(self.intervals) * len(self.rooms) + interval_idx * len(self.rooms) + room_idx
            remaining_steps = total_steps - current_step

        constrangeri_incalcate, materii_neacoperite = check_constraints.check_mandatory_constraints(node, self.input)
        return constrangeri_incalcate == 0 and materii_neacoperite == 0 and remaining_steps == 0
    
    def h(self, node: Timetable):
        day_idx, interval_idx, room_idx = self.get_next_entry(node)
        
        if day_idx == len(self.days):
            remaining_steps = 0
        else:
            total_steps = len(self.days) * len(self.intervals) * len(self.rooms)
            current_step = day_idx * len(self.intervals) * len(self.rooms) + interval_idx * len(self.rooms) + room_idx
            remaining_steps = total_steps - current_step
        
        constrangeri_incalcate, materii_neacoperite = check_constraints.check_mandatory_constraints(node, self.input)
        constrangeri_incalcate += check_constraints.check_optional_constraints(node, self.input)
        return remaining_steps + constrangeri_incalcate + materii_neacoperite

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
            if self.is_final(current_node):
                end = current_node
                break
            open_set.remove(self.node_key(current_node))
            neighbours_ = self.get_neighbours(current_node)
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