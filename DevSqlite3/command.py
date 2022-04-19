# command
from .error import *
from .field import Field


class DatabaseCommand:
    @staticmethod
    def createTableIfNotExists(name, args: dict, mysql=False) -> str:
        has = False
        for item in args:
            if callable(args[item]) or item.startswith("__"):
                continue
            else:
                has = True

        if not has:
            raise NoFieldException(
                "There no variables on your class, for example\n@Database('databaseName')\nclass User(Table):\n\tusername = Table.stringField()\n\tpassword = Table.stringField()\n\t# etc..")

        sql = "create table if not exists {name}(".format(name=name)
        for item in args:
            if callable(args[item]) or item.startswith("__"):
                continue
            else:
                field = Field(item, args[item])

                if field.isField():
                    if field.type() is int:
                        if field.isNull():
                            if field.isPrimary():
                                if mysql:
                                    sql += "{name} INT AUTO_INCREMENT primary key NOT NULL, ".format(name=item)
                                else:
                                    sql += "{name} integer primary key not null, ".format(name=item)
                            else:
                                sql += "{name} integer, ".format(name=item)
                        else:
                            if field.isPrimary():
                                if mysql:
                                    sql += "{name} INT AUTO_INCREMENT primary key NOT NULL, ".format(name=item)
                                else:
                                    sql += "{name} integer primary key not null, ".format(name=item)
                            else:
                                sql += "{name} integer not null, ".format(name=item)

                    elif field.type() is float:
                        if field.isNull():
                            sql += "{name} real, ".format(name=item)
                        else:
                            sql += "{name} real not null, ".format(name=item)

                    elif field.type() == "date":
                        if field.isNull():
                            sql += "{name} real, ".format(name=item)
                        else:
                            sql += "{name} real not null, ".format(name=item)

                    else:
                        if field.isNull():
                            sql += "{name} text, ".format(name=item)
                        else:
                            sql += "{name} text not null, ".format(name=item)
                else:
                    raise ColumnTypeUnknown("Unknown column type, column name {name} type: {typ}".format(name=item, typ=field.type()))

        sql = sql[0: len(sql) - 2].strip()
        sql += ");"
        return sql

    @staticmethod
    def alterTableAdd(name, column, typ) -> str:
        field = Field(column, typ)
        sql = "alter table {name} add column {column} ".format(name=name, column=column)
        if field.isField():
            if field.type() is int:
                if field.isNull():
                    if field.isPrimary():
                        sql += "integer primary key not null"
                    else:
                        sql += "integer"
                else:
                    if field.isPrimary():
                        sql += "integer primary key not null"
                    else:
                        sql += "integer not null"

            elif field.type() is float:
                if field.isNull():
                    sql += "real"
                else:
                    sql += "real not null"

            elif field.type() == "date":
                if field.isNull():
                    sql += "real"
                else:
                    sql += "real not null"

            else:
                if field.isNull():
                    sql += "text"
                else:
                    sql += "text not null"
            sql += ";"
            return sql
        else:
            raise ColumnTypeUnknown(
                "Unknown column type, column name {name} type: {typ}".format(name=column, typ=field.type()))

    @staticmethod
    def alterTableDrop(name, column):
        return "alter table {name} drop {column};".format(name=name, column=column)

    @staticmethod
    def alterTableRenameColumn(name, old, new):
        return "alter table {name} rename column {old} to {new}".format(name=name, old=old, new=new)


class Type:
    @staticmethod
    def integerField(primary=False, null=True) -> dict:
        return {"type": "int()", "primary": primary, "null": null}

    @staticmethod
    def booleanField(null=True) -> dict:
        return {"type": "bool()", "null": null}

    @staticmethod
    def stringField(null=True) -> dict:
        return {"type": "str()", "null": null}

    @staticmethod
    def dictField(null=True) -> dict:
        return {"type": "dict()", "null": null}

    @staticmethod
    def listField(null=True) -> dict:
        return {"type": "list()", "null": null}

    @staticmethod
    def dateField(null=True) -> dict:
        return {"type": "date", "null": null}

    @staticmethod
    def floatField(null=True) -> dict:
        return {"type": "float()", "null": null}

