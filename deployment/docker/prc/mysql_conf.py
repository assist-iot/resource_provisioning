from peewee import *
import os

database = os.environ['MYSQL_DATABASE']
user = os.environ['MYSQL_USER']
password = os.environ['MYSQL_PASSWORD']
host = os.environ['MYSQL_HOST']
port = int(os.environ['MYSQL_PORT'])

db = MySQLDatabase(database, user = user, password = password, host = host, port = port)

class enabler(Model):
    id = PrimaryKeyField()
    name = CharField()
    infer = BooleanField(default=False)
    class Meta:
        database = db

class component(Model):
    id = PrimaryKeyField()
    enabler_id = ForeignKeyField(enabler)
    name = CharField()
    infer = BooleanField(default=False)
    class Meta:
        database = db

class data(Model):
    id = PrimaryKeyField()
    enabler_id = ForeignKeyField(enabler)
    component_id = ForeignKeyField(component)
    timestamp = DateTimeField()
    cpu = IntegerField()
    ram = IntegerField()
    real = BooleanField(default=True)
    class Meta:
        database = db