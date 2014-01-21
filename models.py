from peewee import *
from db import getDbs
term_db, stride_db = getDbs()

class Terms(Model):
    ontology = CharField()
    termid = CharField()
    term = CharField()
    cui = CharField()
    tid = IntegerField()

    class Meta:
        database = term_db # this model uses the people database
        primary_key = CompositeKey('ontology', 'termid', 'cui', 'tid')


class Isaclosure(Model):
    ontology = CharField()
    cid1 = CharField()
    cid2 = CharField()    
    dist = IntegerField()

    class Meta:
        database = term_db # this model uses the people database
        primary_key = CompositeKey('ontology', 'cid1', 'cid2', 'dist')


class Str2cid(Model):
    cid = IntegerField(primary_key=True)
    str = CharField()
    cui = CharField()    
    grp = IntegerField()

    class Meta:
        database = term_db # this model uses the people database
        
class Str2tid(Model):
    tid = IntegerField(primary_key=True)
    str = CharField()
    freq = IntegerField()
    suppress = IntegerField()
    source = CharField()

    class Meta:
        database = term_db # this model uses the people database

class Tid2cid(Model):
    tid = IntegerField()
    cid = IntegerField()
    suppress = IntegerField()    
    grp = IntegerField()
    source = CharField()

    class Meta:
        database = term_db # this model uses the people database


