from peewee import Model, AutoField, SmallIntegerField, UUIDField, DateTimeField
from datetime import datetime


class Game(Model):
    created = DateTimeField(default=datetime.now)
    blue = UUIDField()
    red = UUIDField(null=True)