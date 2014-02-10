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

def closure_term(cid):
	query = "SELECT DISTINCT i1.cid2 AS cid_norm, s1.cui AS cui_norm, s1.str AS str_norm, i2.cid1 AS cid_exp, s2.cui AS cui_exp, s2.str AS str_exp FROM terminology3.str2cid s1, terminology3.str2cid s2, terminology3.isaclosure i1, terminology3.isaclosure i2 WHERE i2.cid1 = s2.cid AND i1.cid2 = s1.cid AND i2.cid2 = i1.cid1 AND s1.cui IN (%s)"
	print >> sys.stderr, 'working in cid '+str(cid)
	result = []
	rows = tryQuery(term_db, query, [cid])
	
	for row in rows:
		d = {
			'cid_norm': row[0],
			'cui_norm': row[1],
			'str_norm': row[2],
			'cid_exp': row[3],
			'cui_exp': row[4],
			'str_exp': row[5]
		}
		result.append(d)
	return result
	
if __name__ == "__main__":
	rt = related_terms(sys.argv[1])	
	result = []
	for t in rt:
		result.extend(closure_term(t['cid']))

	pprint.pprint(result)





