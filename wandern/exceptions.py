class WandernException(Exception):
    pass


class DivergentbranchError(WandernException):
    def __init__(self, from_: str, to_: list[str]) -> None:
        self.from_ = from_
        self.to_ = to_


class InvalidMigrationFile(WandernException):
    pass


class CycleDetected(WandernException):
    def __init__(self, cycle: list) -> None:
        self.cycle = cycle
