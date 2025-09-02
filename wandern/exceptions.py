class WandernException(Exception):
    pass


class DivergentbranchError(WandernException):
    pass


class InvalidMigrationFile(WandernException):
    pass


class GraphErrror(WandernException):
    pass


class CycleDetected(WandernException):
    pass


class ConnectError(WandernException):
    pass
