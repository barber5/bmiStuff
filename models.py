from peewee import *
from db import getDbs
term_db, stride_db = getDbs()

class Term(Model):
    ontology = CharField()
    termid = CharField()
    term = CharField()
    cui = CharField()
    tid = IntegerField()

    class Meta:
        database = term_db # this model uses the people database


sarc = Term.get(Term.term == 'sarcoidosis')
print sarc