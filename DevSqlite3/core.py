# helper

import sqlite3
import os
import pymysql
from .error import *
from typing import Callable
from .command import DatabaseCommand, Type
from .field import Field
import datetime
import warnings

CONNECTION = {"databases": {}}


class Instance:
    @staticmethod
    def get(table: str):
        for db in CONNECTION["databases"]:
            if table in CONNECTION["databases"][db]["classes"]:
                return CONNECTION["databases"][db]["conn"]
        return None

    @staticmethod
    def getSetting(table: str):
        for db in CONNECTION["databases"]:
            if table in CONNECTION["databases"][db]["classes"]:
                return CONNECTION["databases"][db]["settings"]
        return None

    @staticmethod
    def isDatabaseConnected(name):
        if name in CONNECTION["databases"]:
            return True
        return False

    @staticmethod
    def connect(name, path=None, mysql=False, **kwargs):
        kwargs["mysql"] = mysql
        if mysql:
            try:
                conn = pymysql.connect(host=kwargs.get("host"),
                                       port=kwargs.get("port"),
                                       user=kwargs.get("user"),
                                       password=kwargs.get("password"),
                                       charset="utf8",
                                       autocommit=True,
                                       cursorclass=pymysql.cursors.DictCursor)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    conn.cursor().execute("create database if not exists {name}".format(name=name))
                conn.close()
                conn = pymysql.connect(host=kwargs.get("host"),
                                       port=kwargs.get("port"),
                                       user=kwargs.get("user"),
                                       password=kwargs.get("password"),
                                       charset="utf8",
                                       database=name,
                                       autocommit=True,
                                       cursorclass=pymysql.cursors.DictCursor)
                conn.ping(reconnect=True)
            except pymysql.err.OperationalError as w:
                raise DatabaseException("Runtime error: {error}".format(error=w))
            except pymysql.err.InternalError as w:
                raise DatabaseException("Runtime error: {error}".format(error=w))
            except Exception as w:
                raise RuntimeError(f"Unable to connection your database.\nreason: {w}")

            CONNECTION["databases"][name] = {"conn": conn}
            CONNECTION["databases"][name]["classes"] = []
            CONNECTION["databases"][name]["settings"] = kwargs
        else:
            if path:
                if not os.path.exists(path):
                    os.mkdir(path)

                conn = sqlite3.connect("{path}/{name}".format(path=path, name=name), timeout=5, check_same_thread=False)
            else:
                conn = sqlite3.connect(name, timeout=5, check_same_thread=False)

            conn.isolation_level = None
            conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

            CONNECTION["databases"][name] = {"conn": conn}
            CONNECTION["databases"][name]["classes"] = []
            CONNECTION["databases"][name]["settings"] = kwargs

    @staticmethod
    def allowTable(name, table):
        if name in CONNECTION["databases"]:
            CONNECTION["databases"][name]["classes"].append(table)


def MySqlDatabase(database, host=None, user=None, password=None, port=0, **kwargs) -> Callable:
    def wrapper(cls):
        if hasattr(cls, "superclass"):
            base = cls.superclass()
            sup = cls.__base__.__name__
            if base != sup:
                raise DatabaseException(
                    "The database cannot be created because your class is not instance of Table, for example:\n@Database('databaseName')\nclass YourClass(Table):\n\t# etc..")
        else:
            raise DatabaseException(
                "The database cannot be created because your class is not instance of Table, for example:\n@Database('databaseName')\nclass YourClass(Table):\n\t# etc..")

        Instance.connect(database, mysql=True, host=host, user=user, password=password, port=port, **kwargs)
        Instance.allowTable(database, cls.__name__)
        cls().init(mysql=True)
        return cls

    return wrapper


def Database(name, path=None, **kwargs) -> Callable:
    def wrapper(cls):
        if hasattr(cls, "superclass"):
            base = cls.superclass()
            sup = cls.__base__.__name__
            if base != sup:
                raise DatabaseException(
                    "The database cannot be created because your class is not instance of Table, for example:\n@Database('databaseName')\nclass YourClass(Table):\n\t# etc..")
        else:
            raise DatabaseException(
                "The database cannot be created because your class is not instance of Table, for example:\n@Database('databaseName')\nclass YourClass(Table):\n\t# etc..")
        if not Instance.isDatabaseConnected(name):
            Instance.connect(name, path=path, **kwargs)
            Instance.allowTable(name, cls.__name__)
        else:
            Instance.allowTable(name, cls.__name__)
        cls().init()
        return cls

    return wrapper


class Table(Type):
    def __init__(self):
        self.tableName = self.__class__.__name__
        self.__database = Instance.get(self.__class__.__name__)
        self.isMySql = Instance.getSetting(self.tableName).get("mysql")

    def init(self, mysql=False):
        self.isMySql = mysql
        if self.__database is None:
            raise DatabaseException(
                "did you forget to decorator your class with @Database('name') or @MySqlDatabase('name')?")
        c = DatabaseCommand.createTableIfNotExists(self.tableName, self.__class__.__dict__, mysql=self.isMySql)
        if not c.count("primary key"):
            raise DatabaseException(
                "One of the variables must be of type primary key, for example:\n id = Table.integerField(primary=True, null=False)")
        self.__execute(c)
        if self.isMySql:
            self.__columnsModifyMySQL()
        else:
            self.__columnsModify()

    def __setattr__(self, key, value):
        items = self.__parser(self.__class__.__dict__)
        if key in items:
            field = Field(key, items[key])
            if field.isPrimary() and key in self.__dict__:
                raise NotAllowed("it is not possible to change primary value for {var}".format(var=key))

        self.__dict__[key] = value

    def __columnsModify(self):
        cursor = self.__database.cursor()
        columns = cursor.execute("PRAGMA table_info({name})".format(name=self.tableName)).fetchall()
        cursor.close()
        dItems = self.__class__.__dict__
        items = list(filter(lambda i: not callable(dItems[i]) and not i.startswith("__"), dItems))

        # drop column if variable not exists on class
        setting = Instance.getSetting(self.tableName)
        dropEnable = setting.get("dropColumnNotExists") if setting.get("dropColumnNotExists") is not None else True
        addEnable = setting.get("addColumnNotExists") if setting.get("addColumnNotExists") is not None else True
        if dropEnable:
            for column in columns:
                if any(column["name"] == item for item in items):
                    continue
                else:
                    self.alterTableDropColumn(column["name"])

        # add column if variable name not exists on table
        if addEnable:
            for item in items:
                if any(item == column["name"] for column in columns):
                    continue
                self.alterTableAddColumn(item, dItems[item])

    def __columnsModifyMySQL(self):
        cursor = self.__database.cursor()
        cursor.execute("show columns from {name}".format(name=self.tableName))
        columns = cursor.fetchall()
        cursor.close()
        dItems = self.__class__.__dict__
        items = list(filter(lambda i: not callable(dItems[i]) and not i.startswith("__"), dItems))

        # drop column if variable not exists on class
        setting = Instance.getSetting(self.tableName)
        dropEnable = setting.get("dropColumnNotExists") if setting.get("dropColumnNotExists") is not None else True
        addEnable = setting.get("addColumnNotExists") if setting.get("addColumnNotExists") is not None else True
        if dropEnable:
            for column in columns:
                if any(column["Field"] == item for item in items):
                    continue
                else:
                    self.alterTableDropColumn(column["Field"])

        # add column if variable name not exists on table
        if addEnable:
            for item in items:
                if any(item == column["Field"] for column in columns):
                    continue
                self.alterTableAddColumn(item, dItems[item])

    @staticmethod
    def superclass():
        return Table.__name__

    def alterTableAddColumn(self, column, typ):
        c = DatabaseCommand.alterTableAdd(self.tableName, column, typ)
        self.__alter_execute(c)

    def alterTableDropColumn(self, column):
        c = DatabaseCommand.alterTableDrop(self.tableName, column)
        self.__alter_execute(c)

    def alterTableRenameColumn(self, oldName, newName):
        c = DatabaseCommand.alterTableRenameColumn(self.tableName, oldName, newName)
        self.__alter_execute(c)

    @staticmethod
    def __parser(items):
        variables = dict()
        for item in items:
            if callable(items[item]) or item.endswith("__"):
                continue
            variables[item] = items[item]
        return variables

    def __insert(self, changed, primary):
        if primary:
            del changed[primary]

        if self.isMySql:
            if len(changed) > 1:
                sql = "insert into {table}{data} values {date_info}".format(table=self.tableName,
                                                                            data=tuple(changed.keys()),
                                                                            date_info=tuple(['%s' for x in changed]))
            else:
                sql = "insert into {table}{data} values {date_info}".format(table=self.tableName,
                                                                            data="({})".format(list(changed.keys())[0]),
                                                                            date_info="(%s)")
        else:
            if len(changed) > 1:

                sql = "insert into {table}{data} values {date_info}".format(table=self.tableName,
                                                                            data=tuple(changed.keys()),
                                                                            date_info=tuple(['?' for x in changed]))
            else:
                sql = "insert into {table}{data} values {date_info}".format(table=self.tableName,
                                                                            data="({})".format(list(changed.keys())[0]),
                                                                            date_info="(?)")
        sql = sql.replace("'", "")
        return self.__execute(sql, tuple(changed.values()))

    def __update(self, changed, primary):
        find = changed[primary]
        del changed[primary]
        sql = "update {table} set ".format(table=self.tableName)
        for key in changed:
            sql += "{key}=:{key}, ".format(key=key, value=changed[key])
        sql = sql[:-2]
        sql += " where {primary}={primaryValue}".format(primary=primary, primaryValue=find)
        if self.isMySql:
            self.__mysql_execute(sql, changed)
        else:
            self.__execute(sql, changed)
        return find

    def delete(self):
        variables = self.__parser(self.__class__.__dict__)
        changed = self.__dict__
        sql = ""
        for var in changed:
            if var in variables:
                if changed[var] is None:
                    continue
                if type(changed[var]) is bool:
                    continue
                if type(changed[var]) is list:
                    continue
                if type(changed[var]) is dict:
                    continue
                else:
                    sql += "{var}=:{var} and ".format(var=var)
        if sql:
            sql = sql[:-4]
            sql = "delete from {table} where {sql}".format(table=self.tableName, sql=sql)
            if self.isMySql:
                self.__mysql_execute(sql, changed)
            else:
                self.__execute(sql, changed)
            return True
        return False

    def save(self):
        variables = self.__parser(self.__class__.__dict__)
        changed = self.__dict__
        insert = True
        primary = None
        _class = None
        keyValue = dict()
        for var in changed:
            if var in variables:
                field = Field(var, variables[var])
                c_typ = type(changed[var])
                f_typ = field.type()
                if c_typ is not f_typ and c_typ.__name__ != "datetime" and f_typ != "date":
                    if not field.isNull():
                        raise DatabaseException(
                            "save error, variable {var} type {typ}, can't be type {typ1}, not null field detected".format(
                                var=var,
                                typ=f_typ.__name__,
                                typ1=c_typ.__name__))
                    elif c_typ.__name__ != "NoneType":
                        raise DatabaseException(
                            "save error, variable {var} type {typ}, can't be type {typ1}".format(var=var,
                                                                                                 typ=f_typ.__name__,
                                                                                                 typ1=c_typ.__name__))
                value = changed[var]
                if c_typ is dict:
                    value = str(value)
                elif c_typ is list:
                    value = str(value)
                elif c_typ == "date":
                    value = str(value.timestamp())

                keyValue[var] = value
                if field.isPrimary():
                    primary = var
                    r = self.execute(
                        "select * from {table} where {var}=:var".format(table=self.tableName, var=var),
                        args={"var": changed[var]}).first()
                    if r:
                        _class = r
                        insert = False
                    else:
                        insert = True

        if _class:
            changed = False
            for keyV in keyValue:
                v = keyValue[keyV]
                cv = eval("_class.{}".format(keyV))
                if v != cv:
                    changed = True
            if not changed:
                return "no changed detected, ignore"

        if insert:
            return self.__insert(keyValue, primary)
        else:
            return self.__update(keyValue, primary)

    class __Where:
        def __init__(self, cls, database, where):
            self.__cls = cls
            self.__database = database
            self.__where = {where: {"target": None, "fix": None, "or": False}}
            self.__sql = ""
            self.__values = ()

        def orWhere(self, variable):
            for where in self.__where:
                if self.__where[where]["target"] is None:
                    raise WhereUsageException(
                        "To use orWhere, You have to finish first where, for example:\nclass.where('username').equals('any')\nthen you can call orWhere, another example:\n\nclass.where('username').notEquals('any').orWhere('username').equals('any').first()")
            self.__where[variable] = {}
            self.__where[variable]["target"] = None
            self.__where[variable]["fix"] = None
            self.__where[variable]["or"] = True
            return self

        def andWhere(self, variable):
            for where in self.__where:
                if self.__where[where]["target"] is None:
                    raise WhereUsageException(
                        "To use andWhere, You have to finish first where, for example:\nclass.where('username').equals('any')\nthen you can call andWhere, another example:\n\nclass.where('username').notEquals('any').andWhere('username').equals('any').first()")
            self.__where[variable] = {}
            self.__where[variable]["target"] = None
            self.__where[variable]["fix"] = None
            self.__where[variable]["or"] = False
            return self

        def equals(self, value):
            if type(value).__name__ not in ["int", "str", "bool"]:
                raise WhereUsageException(
                    "parameter type {info} can't be detected on database, please use [str, int, bool]".format(
                        info=type(value).__name__))

            for where in self.__where:
                if self.__where[where]["target"] is None:
                    self.__where[where]["target"] = value
                    self.__where[where]["fix"] = "="
            self.__translatorSqlite(value)
            return self

        def notEquals(self, value):
            if type(value).__name__ not in ["int", "str", "bool"]:
                raise WhereUsageException(
                    "parameter type {info} can't be detected on database, please use [str, int, bool]".format(
                        info=type(value).__name__))
            for where in self.__where:
                if self.__where[where]["target"] is None:
                    self.__where[where]["target"] = value
                    self.__where[where]["fix"] = "!="
            self.__translatorSqlite(value)
            return self

        def like(self, value, before=True, after=True):
            if type(value).__name__ not in ["int", "str", "bool"]:
                raise WhereUsageException(
                    "parameter type {info} can't be detected on database, please use [str, int, bool]".format(
                        info=type(value).__name__))
            if before:
                value = "%{v}".format(v=value)
            if after:
                value = "{v}%".format(v=value)

            for where in self.__where:
                if self.__where[where]["target"] is None:
                    self.__where[where]["target"] = value
                    self.__where[where]["fix"] = "like"
            self.__translatorSqlite(value)
            return self

        def notLike(self, value, before=True, after=True):
            if type(value).__name__ not in ["int", "str", "bool"]:
                raise WhereUsageException(
                    "parameter type {info} can't be detected on database, please use [str, int, bool]".format(
                        info=type(value).__name__))
            if before:
                value = "%{v}".format(v=value)
            if after:
                value = "{v}%".format(v=value)

            for where in self.__where:
                if self.__where[where]["target"] is None:
                    self.__where[where]["target"] = value
                    self.__where[where]["fix"] = "not like"
            self.__translatorSqlite(value)
            return self

        def orderBy(self, variable, stuff="asc", limit=0):
            if type(variable).__name__ not in ["int", "str", "bool"]:
                raise WhereUsageException(
                    "parameter type {info} can't be detected on database, please use [str, int, bool]".format(
                        info=type(variable).__name__))
            if self.__sql:
                if limit > 0:
                    self.__sql += " order by {} {} limit {}".format(variable, stuff, limit)
                else:
                    self.__sql += " order by {} {}".format(variable, stuff)
            else:
                if limit > 0:
                    self.__sql = " order by {} {} limit {}".format(variable, stuff, limit)
                else:
                    self.__sql = " order by {} {}".format(variable, stuff)
            return self

        def all(self, asDict=False):
            sql = "select * from {table}".format(table=self.__cls.__class__.__name__)
            if self.__sql:
                if self.__sql.startswith(" order"):
                    sql += self.__sql
                else:
                    sql += " where {sql}".format(sql=self.__sql)
            cursor = self.__database.cursor()
            if self.__cls.isMySql:
                cursor.execute(sql, self.__values)
                fetch = cursor.fetchall()
            else:
                fetch = cursor.execute(sql, self.__values).fetchall()
            cursor.close()
            if asDict:
                return fetch
            result = list()
            for row in fetch:
                cls = self.__cls.__class__()
                for column in row:
                    value = self.__cls.change(column, row)
                    setattr(cls, column, value)
                result.append(cls)
            return result

        def first(self, asDict=False):
            sql = "select * from {table}".format(table=self.__cls.__class__.__name__)
            if self.__sql:
                if self.__sql.startswith(" order"):
                    sql += self.__sql
                else:
                    sql += " where {sql}".format(sql=self.__sql)
            cursor = self.__database.cursor()
            if self.__cls.isMySql:
                cursor.execute(sql, self.__values)
                fetch = cursor.fetchone()
            else:
                fetch = cursor.execute(sql, self.__values).fetchone()
            cursor.close()
            if asDict:
                return fetch
            if not fetch:
                return None
            cls = self.__cls.__class__()
            for column in fetch:
                value = self.__cls.change(column, fetch)
                setattr(cls, column, value)
            return cls

        def __translatorSqlite(self, variable):
            for where in self.__where:
                if self.__where[where]["target"] != variable:
                    continue

                self.__values = self.__values + (variable,)
                if self.__where[where]["or"]:
                    if self.__sql:
                        if self.__cls.isMySql:
                            self.__sql += " or {var} {fix} %s".format(var=where, fix=self.__where[where]["fix"])
                        else:
                            self.__sql += " or {var} {fix} ?".format(var=where, fix=self.__where[where]["fix"])
                else:
                    if self.__sql:
                        if self.__cls.isMySql:
                            self.__sql += " and {var} {fix} %s".format(var=where, fix=self.__where[where]["fix"])
                        else:
                            self.__sql += " and {var} {fix} ?".format(var=where, fix=self.__where[where]["fix"])
                    else:
                        if self.__cls.isMySql:
                            self.__sql += "{var} {fix} %s".format(var=where, fix=self.__where[where]["fix"])
                        else:
                            self.__sql += "{var} {fix} ?".format(var=where, fix=self.__where[where]["fix"])

    def where(self, variable):
        return self.__Where(self, self.__database, variable)

    def __alter_execute(self, c):
        cursor = self.__database.cursor()
        try:
            cursor.execute(c)
        except sqlite3.OperationalError:
            cursor.close()

    class __Execute:
        def __init__(self, cls, database, command, args: dict = None):
            self.cls = cls
            self.database = database
            self.command = command
            self.args = args

        def all(self, asDict=False):
            if self.args:
                if self.cls.isMySql:
                    cursor = self.cls.mysql_cursor(self.command, self.args)
                    res = cursor.fetchall()
                else:
                    cursor = self.database.cursor()
                    res = cursor.execute(self.command, self.args).fetchall()
            else:
                if self.cls.isMySql:
                    cursor = self.cls.mysql_cursor(self.command)
                    res = cursor.fetchall()
                else:
                    cursor = self.database.cursor()
                    res = cursor.execute(self.command).fetchall()
            cursor.close()
            if asDict:
                return res

            result = list()
            for row in res:
                cls = self.cls.__class__()
                for column in row:
                    value = self.cls.change(column, row)
                    setattr(cls, column, value)
                result.append(cls)
            return result

        def first(self, asDict=False):
            if self.args:
                if self.cls.isMySql:
                    cursor = self.cls.mysql_cursor(self.command, self.args)
                    res = cursor.fetchone()
                    cursor.close()
                else:
                    cursor = self.database.cursor()
                    res = cursor.execute(self.command, self.args).fetchone()
            else:
                if self.cls.isMySql:
                    cursor = self.cls.mysql_cursor(self.command)
                    res = cursor.fetchone()
                    cursor.close()
                else:
                    cursor = self.database.cursor()
                    res = cursor.execute(self.command).fetchone()
            cursor.close()
            if asDict:
                return res

            if not res:
                return None
            cls = self.cls.__class__()
            for column in res:
                value = self.cls.change(column, res)
                setattr(cls, column, value)
            return cls

        def run(self):
            if self.args:
                if self.cls.isMySql:
                    cursor = self.cls.mysql_cursor(self.command, self.args)
                else:
                    cursor = self.database.cursor()
                    cursor.execute(self.command, self.args)
            else:
                if self.cls.isMySql:
                    cursor = self.cls.mysql_cursor(self.command)
                else:
                    cursor = self.database.cursor()
                    cursor.execute(self.command)

            i = cursor.rowcount
            cursor.close()
            return i

    def execute(self, command, args: dict = None) -> __Execute:
        return self.__Execute(self, self.__database, command, args)

    def change(self, k, d):
        dItems = self.__class__.__dict__
        if k in dItems:
            field = Field(k, dItems[k])
            if k in d:
                value = d[k]
                if value is not None:
                    if field.type() is int:
                        value = int(value)
                    elif field.type() is str:
                        value = str(value)
                    elif field.type() is dict:
                        value = eval(value)
                    elif field.type() is bool:
                        value = bool(eval(value))
                    elif field.type() is list:
                        value = eval(value)
                    elif field.type() == "date":
                        value = datetime.datetime.fromtimestamp(float(value))
            else:
                raise DatabaseException("Unknown column: {k}".format(k=k))
        else:
            raise DatabaseException("Unknown column: {k}".format(k=k))
        return value

    def __execute(self, command, args=None):
        cursor = self.__database.cursor()
        try:
            if args:
                cursor.execute(command, args)
            else:
                cursor.execute(command)
        except Exception as arg:
            raise DatabaseException(arg)
        last = cursor.lastrowid
        cursor.close()
        return last

    def __mysql_execute(self, command, args=None):
        if args is None:
            args = {}
        cursor = self.__database.cursor()
        try:
            if args:
                values = []
                for key in args:
                    if command.count(":{}".format(key)):
                        command = command.replace(":{}".format(key), "%s")
                        values.append(args[key])
                if len(values) > 1:
                    cursor.execute(command, tuple(values))
                else:
                    cursor.execute(command, values[0])
            else:
                cursor.execute(command)
        except Exception as arg:
            raise DatabaseException(arg)
        last = cursor.lastrowid
        cursor.close()
        return last

    def mysql_cursor(self, command, args=None):
        cursor = self.__database.cursor()
        if args:
            values = []
            for key in args:
                command = command.replace(":{}".format(key), "%s")
                values.append(args[key])
            if len(values) > 1:
                cursor.execute(command, tuple(values))
            else:
                cursor.execute(command, values[0])
        else:
            cursor.execute(command)
        return cursor

