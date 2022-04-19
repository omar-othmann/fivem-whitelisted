from DevSqlite3.core import MySqlDatabase, Table, Database
from config import Config


@MySqlDatabase(Config.select, host=Config.ip, user=Config.user, password=Config.password)
class Whitelist(Table):
    id = Table.integerField(primary=True, null=False)
    discord = Table.integerField()
    whitelisted = Table.booleanField()


@Database('settings', path='database')
class Settings(Table):
    id = Table.integerField(primary=True, null=False)
    autoRemove = Table.booleanField()
    autoGiver = Table.booleanField()
    managers = Table.listField()

    def getAll(self):
        return self.execute('select * from settings').first()
