# field
from .error import *


class Field:
    def __init__(self, name, field):
        self.name = name
        self.field = field

    def type(self):
        if "type" in self.field:
            typ = self.field["type"]
            return typ if typ == "date" else type(eval(typ))
        else:
            raise ColumnTypeUnknown("Unknown column type, column name {name}".format(name=self.name))

    def isNull(self):
        return self.field["null"]

    def isPrimary(self):
        if "primary" in self.field:
            return self.field["primary"]
        return False

    def isField(self):
        return "type" in self.field

    def canInsert(self, value):
        return True if self.type() == type(value) or self.type() == "date" and type(value).__name__ == "datetime" else False

    def __str__(self):
        pass

