from abc import ABC, abstractmethod

class SolveStrategy(ABC):
    @abstractmethod
    def solve(self, input):
        pass