class SolveContext:
    def __init__(self, strategy):
        self.strategy = strategy

    def perform_solve(self, input):
        self.strategy.solve(input)

    def set_solving_strategy(self, strategy):
        self.strategy = strategy