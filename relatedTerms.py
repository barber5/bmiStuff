from db import *
import sys


(term_db, stride_db) = getDbs()

def related_terms(term_query):
	query = "SELECT t5.tid as tid, t5.str as str, t2.cid as cid FROM terms AS t1 INNER JOIN tid2cid AS t2 ON (t2.tid = t1.tid) INNER JOIN isaclosure AS t3 ON (t2.cid = t3.cid1) INNER JOIN isaclosure AS t6 ON (t3.cid1 = t6.cid2) INNER JOIN tid2cid AS t4 ON (t4.cid = t6.cid2) INNER JOIN str2tid AS t5 ON (t4.tid = t5.tid) WHERE (t1.term = %s) group by t5.tid"

	rows = tryQuery(term_db, query, [term_query])
	for row in rows:
		print row
	
	
if __name__ == "__main__":
	rt = related_terms(sys.argv[1])	