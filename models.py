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
        primary_key = CompositeKey('tid', 'cid', 'grp', 'source', 'suppress')


term_query = 'sarcoidosis'
t1 = Tid2cid.alias()
t2 = Tid2cid.alias()
i1 = Isaclosure.alias()
i2 = Isaclosure.alias()
st = Str2tid.alias()
tms = Terms.select(t2).where(Terms.term == term_query).join(t1, on=(t1.tid==Terms.tid)).join(i1, on=(t1.cid==i1.cid1)).join(i2, on=(i1.cid1==i2.cid2)).join(t2, on=(t2.cid==i2.cid2)).join(st, on=(t2.tid==st.tid)).limit(20)
print tms
res = tms.execute()
for r in res:
	print r.str	

