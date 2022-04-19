# errors

class NotAllowed(Exception):
    """when change class.id"""


class DatabaseException(Exception):
    """Database error"""


class ColumnTypeUnknown(Exception):
    """Variable type unknown"""


class NoFieldException(Exception):
    """Class has no variables"""


class WhereUsageException(Exception):
    """Detected error when you use class.where"""










