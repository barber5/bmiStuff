from db import *
import sys, pprint


(term_db, stride_db) = getDbs()

def related_terms(term_query):	
	query = "SELECT s1.tid, s1.str, t2.cid FROM terms INNER JOIN tid2cid t1 on terms.tid=t1.tid INNER JOIN tid2cid t2 on t1.cid=t2.cid inner join str2tid s1 on s1.tid=t2.tid where(terms.term=%s) group by s1.tid"

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