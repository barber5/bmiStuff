from db import *
import sys, pprint


(term_db, stride_db) = getDbs()

def related_terms(term_query):
	query = "SELECT t1.tid as tid, s1.str as str, t4.cid as cid FROM terms AS t1 INNER JOIN tid2cid AS t2 ON (t2.tid = t1.tid) INNER JOIN isaclosure AS i1 ON (t2.cid = i1.cid1) INNER JOIN isaclosure AS i2 ON (i1.cid1 = i2.cid2) INNER JOIN tid2cid AS t4 ON (t4.cid = i2.cid2) INNER JOIN str2tid AS s1 ON (t4.tid = s1.tid) WHERE (t1.term = %s) group by s1.tid"

	rows = tryQuery(term_db, query, [term_query])
	result = []
	for row in rows:
		d = {
			'tid': row[0],
			'term': row[1],
			'cid': row[2]
		}
		result.append(d)
	return result

	
if __name__ == "__main__":
	rt = related_terms(sys.argv[1])	
	pprint.pprint(rt)