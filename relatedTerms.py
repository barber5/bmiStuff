from models import *
import sys

def related_terms(term_query):
	Isa2 = Isaclosure.alias()
	tms = Terms.select().where(Terms.term == term_query).join(Tid2cid.join(Isaclosure.join(Isa2, on=(Isa2.cid2=Isaclosure.cid1)), on=(Tid2cid.cid=Isaclosure.cid1)), on=(Tid2cid.tid==Terms.tid))
	print tms

if __name__ == "__main__":
	rt = related_terms(sys.argv[1])
	for r in rt:
		print r