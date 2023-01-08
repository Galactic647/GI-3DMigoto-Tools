class OutOfScopeError(Exception):
    """Raised when calling a command outside of scope"""


class SlotNotFoundError(Exception):
    """Raised when trying to get non-existent slot"""


class CommandNotFoundError(Exception):
    """Raised when trying to get non-existent command"""


class CommandError(Exception):
    pass
