from utils import *
from ast import literal_eval
from copy import deepcopy
from heapq import *

class Node:
    def __init__(self, schedule):
        self.schedule = schedule
    def __lt__(self, other):
        return True

class ASTAR:
    def __init__(self, file_name):
        self.file_name = file_name
        self.constraints = read_yaml_file(file_name)
        self.start = Node(self.init_schedule())
        self.soft_restrictions = self.build_soft_restrictions()
        self.no_generated_nodes = 0

    def get_intervals(self):
        intervals = [literal_eval(interval) for interval in self.constraints[INTERVALE]]
        return intervals

    def init_schedule(self):
        days = self.constraints[ZILE]
        intervals = self.get_intervals()
        schedule = {day: {} for day in days}
        for day in days:
            for interval in intervals:
                schedule[day][interval] = {}
        return schedule
    
    def get_no_students_unassigned(self, node: Node):
        subject_total_capacity = {subject: 0 for subject in self.constraints[MATERII].keys()}
        days = self.constraints[ZILE]
        intervals = self.get_intervals()
        for day in days:
            for interval in intervals:
                subjects = [course_info[1] for course_info in node.schedule[day][interval].values() if course_info is not None]
                rooms = [room for room in node.schedule[day][interval].keys()]
                for subject, room in list(zip(subjects, rooms)):
                    room_capacity = self.constraints[SALI][room]['Capacitate']
                    subject_total_capacity[subject] += room_capacity
        no_students_unassigned = 0
        for subject in self.constraints[MATERII].keys():
            if subject_total_capacity[subject] < self.constraints[MATERII][subject]:
                no_students_unassigned += self.constraints[MATERII][subject] - subject_total_capacity[subject]
        return no_students_unassigned
    
    def good_work_load(self, professor: str):

        def helper(node: Node):
            work_load = 0
            days = self.constraints[ZILE]
            intervals = self.get_intervals()
            for day in days:
                for interval in intervals:
                    profs = [course_info[0] for course_info in node.schedule[day][interval].values() if course_info is not None]
                    if professor in profs:
                        work_load += 1
            return work_load <= 7
        return helper

    def is_final(self, node: Node):
        return self.get_no_students_unassigned(node) == 0
    
    def is_good(self, node: Node):
        def same_prof_not_multiple_times_same_interval(day: str, interval: tuple[int, int]):
            def helper(node: Node):
                profs = [course_info[0] for course_info in node.schedule[day][interval].values() if course_info is not None]
                return len(profs) == len(set(profs))
            return helper
        days = self.constraints[ZILE]
        intervals = self.get_intervals()
        for day in days:
            for interval in intervals:
                if not same_prof_not_multiple_times_same_interval(day, interval)(node):
                    return False
        for prof in self.constraints[PROFESORI].keys():
            if not self.good_work_load(prof)(node):
                return False
        return True
    
    def get_values(self, room):
        values = []
        for professor in self.constraints[PROFESORI].keys():
            for subject in self.constraints[PROFESORI][professor][MATERII]:
                if subject in self.constraints[SALI][room][MATERII]:
                    values.append((professor, subject))
        values.append(None)
        return values
    
    def get_neighbours(self, node: Node):
        def build_neighbour(node: Node, day, interval, room, val):
            new_node = deepcopy(node)
            new_node.schedule[day][interval][room] = val
            return new_node
        days = self.constraints[ZILE]
        intervals = self.get_intervals()
        for day in days:
            for interval in intervals:
                for room in self.constraints[SALI].keys():
                    if room not in node.schedule[day][interval].keys():
                        neighbours = []
                        for value in self.get_values(room):
                            neighbour = build_neighbour(node, day, interval, room, value)
                            neighbours.append(neighbour)
                        return list(filter(self.is_good, neighbours))
        return []
    
    def h(self, node: Node):
        return 1 * self.get_no_students_unassigned(node) + 1 * self.get_no_breached_soft_restrictions(node)
    
    def g(self, node: Node):
        return 0
    
    def day_preference(self, professor: str, day: str, prefered_on_day: bool):
        def helper(node: Node):
            intervals = self.get_intervals()
            teaches_on_day = False
            times = 0
            for interval in intervals:
                profs = [course_info[0] for course_info in node.schedule[day][interval].values() if course_info is not None]
                teaches_on_day = teaches_on_day or (professor in profs)
                if professor in profs:
                    times += 1
            return (teaches_on_day == prefered_on_day, times)
        return helper
    
    def interval_inclusion(self, interval1, interval2):
        """
            Args:
                interval1: tuple(start, end).
                interval2: tuple(start, end).
            Returns:
                True if interval1 is contained within interval2 else False.
        """
        return interval1[0] >= interval2[0] and interval1[1] <= interval2[1]
    
    def interval_preference(self, professor: str, hours: tuple[int, int], prefered_in_hours: bool):
        def helper(node: Node):
            days = self.constraints[ZILE]
            intervals = self.get_intervals()

            teaches_in_interval = False
            times = 0
            for day in days:
                for interval in intervals:
                    profs = [course_info[0] for course_info in node.schedule[day][interval].values() if course_info is not None]
                    if self.interval_inclusion(interval, hours):
                        teaches_in_interval = teaches_in_interval or (professor in profs)
                        if professor in profs:
                            times += 1
            return (teaches_in_interval == prefered_in_hours, times)
        return helper
    
    def pause_preference(self, professor: str, pause: int, pause_is_less: bool):
        def intervals_diff(interval1, interval2):
            return interval1[0] - interval2[1]
        def helper(node: Node):
            days = self.constraints[ZILE]
            intervals = self.get_intervals()
            pause_is_less_ = True
            times = 0
            for day in days:
                prof_intervals = []
                for interval in intervals:
                    profs = [course_info[0] for course_info in node.schedule[day][interval].values() if course_info is not None]
                    if professor in profs:
                        prof_intervals.append(interval)
                for i in range(len(prof_intervals) - 1):
                    pause_is_less_ = pause_is_less_ and (intervals_diff(prof_intervals[i + 1], prof_intervals[i]) < pause)
                    if (intervals_diff(prof_intervals[i + 1], prof_intervals[i]) > pause):
                        times += 1
            return (pause_is_less_ == pause_is_less, times)
        return helper
    
    def parse_restriction(self, restriction: str):
        original_restriction = restriction
        restriction = restriction.lstrip('!')

        if restriction.__contains__('-'):
            parts = restriction.split('-')
            interval = int(parts[0]), int(parts[1])
            return ('Interval', interval, not original_restriction.startswith('!'))
        
        if restriction.startswith('Pauza'):
            return ('Pauza', int(restriction.split()[2]), restriction.split()[1] == '<')
        
        days = self.constraints[ZILE]
        
        for day in days:
            if restriction.startswith(day):
                return ('Zi', day, not original_restriction.startswith('!'))

    def build_soft_restrictions(self):
        restrictions = []
        constraints = self.constraints
        professors = constraints[PROFESORI].keys()

        for professor in professors:
            prof_constraints = constraints[PROFESORI][professor]['Constrangeri']
            for restriction in prof_constraints:
                parsed_restriction = self.parse_restriction(restriction)
                if parsed_restriction[0] == 'Zi':
                    day = parsed_restriction[1]
                    prefered_on_day = parsed_restriction[2]
                    restrictions.append((self.day_preference, [professor, day, prefered_on_day]))
                elif parsed_restriction[0] == 'Interval':
                    interval = parsed_restriction[1]
                    prefered_in_hours = parsed_restriction[2]
                    restrictions.append((self.interval_preference, [professor, interval, prefered_in_hours]))
                elif parsed_restriction[0] == 'Pauza':
                    pause = parsed_restriction[1]
                    pause_is_less = parsed_restriction[2]
                    restrictions.append((self.pause_preference, [professor, pause, pause_is_less]))

        return restrictions
    
    def get_no_breached_soft_restrictions(self, node: Node):
        breached = 0
        for restriction in self.soft_restrictions:
            res = restriction[0](*restriction[1])(node)
            if not res[0]:
                breached += res[1]
        return breached

    def get_constraints_dictionary(self):
        return read_yaml_file(self.file_name)
    
    def astar(self, start: Node, g, h, neighbours, is_final, acceptable_cost):
        frontier = []
        heappush(frontier, (0 + h(start), start))
        no_generated_nodes = 1
        g_score = {}
        g_score[start] = g(start)
        res = None
        while frontier:
            current = heappop(frontier)[1]
            if is_final(current):
                res = current
                if (h(res) <= acceptable_cost):
                    break
            for neighbour in neighbours(current):
                no_generated_nodes += len(neighbours(current))
                t_g = g(neighbour)
                if neighbour not in g_score:
                    g_score[neighbour] = float('inf')
                if t_g < g_score[neighbour]:
                    g_score[neighbour] = t_g
                    if neighbour not in frontier:
                        heappush(frontier, (t_g + h(neighbour), neighbour))
        return res
    
    def solve(self):
        return self.complete_solution(self.astar(self.start, self.g, self.h, self.get_neighbours, self.is_final, 100))
    
    def complete_solution(self, final_node: Node):
        days = self.constraints[ZILE]
        intervals = self.get_intervals()
        for day in days:
            for interval in intervals:
                for room in self.constraints[SALI].keys():
                    if room not in final_node.schedule[day][interval].keys():
                        final_node.schedule[day][interval][room] = None
        return final_node
    