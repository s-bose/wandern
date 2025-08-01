class WandernException(Exception):
    pass


class DivergentbranchError(WandernException):
    pass


class InvalidMigrationFile(WandernException):
    pass


class GraphErrror(WandernException):
    pass


class CycleDetected(WandernException):
    def __init__(self, cycle: list) -> None:
        self.cycle = cycle
