from db import *
import sys


(term_db, stride_db) = getDbs()

def related_terms(term_query):
	query = "SELECT DISTINCT s1.cid as tid, s1.str as str, t2.cid as cid, 'fwd' as direction FROM terms AS t1 INNER JOIN tid2cid AS t2 ON (t2.tid = t1.tid) INNER JOIN isaclosure AS i1 ON (t2.cid = i1.cid2) INNER JOIN isaclosure AS i2 ON (i2.cid2 = i1.cid1)  INNER JOIN str2cid AS s1 ON (i2.cid2 = s1.cid) WHERE (t1.term = %s) UNION SELECT DISTINCT s1.cid as tid, s1.str as str, t2.cid as cid, 'rev' as direction FROM terms AS t1 INNER JOIN tid2cid AS t2 ON (t2.tid = t1.tid) INNER JOIN isaclosure AS i1 ON (t2.cid = i1.cid1) INNER JOIN isaclosure AS i2 ON (i2.cid1 = i1.cid2)  INNER JOIN str2cid AS s1 ON (i2.cid1 = s1.cid) WHERE (t1.term = %s) UNION SELECT DISTINCT s1.cid as tid, s1.str as str, t2.cid as cid, 'par' as direction FROM terms AS t1 INNER JOIN tid2cid AS t2 ON (t2.tid = t1.tid) INNER JOIN isaclosure AS i1 ON (t2.cid = i1.cid1) INNER JOIN isaclosure AS i2 ON (i2.cid1 = i1.cid2)  INNER JOIN str2cid AS s1 ON (i2.cid2 = s1.cid) WHERE (t1.term = %s);"

	rows = tryQuery(term_db, query, [term_query, term_query])
	for row in rows:
		print row
	print len(rows)
	
if __name__ == "__main__":
	rt = related_terms(sys.argv[1])	