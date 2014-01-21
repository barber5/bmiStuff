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


sarc = Terms.get(Terms.term == 'sarcoidosis')
print sarc