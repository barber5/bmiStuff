from models import *
import sys

def related_terms(term_query):
	t1 = Tid2cid.alias()
	t2 = Tid2cid.alias()
	i1 = Isaclosure.alias()
	i2 = Isaclosure.alias()
	st = Str2tid.alias()
	tms = Terms.select(Terms, t2).where(Terms.term == term_query).join(t1, on=(t1.tid==Terms.tid)).join(i1, on=(t1.cid==i1.cid1)).join(i2, on=(i1.cid1==i2.cid2)).join(t2, on=(t2.cid==i2.cid2)).join(st, on=(t2.tid==st.tid)).limit(20)
	print tms
	res = tms.execute()
	for r in res:
		print r
		print r.t2
		print r.str	

if __name__ == "__main__":
	rt = related_terms(sys.argv[1])
	for r in rt:
		print r