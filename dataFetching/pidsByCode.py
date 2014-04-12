from db import *
import sys, pprint, threading, json, os, time, copy



def srcTypeConditional(types):
	query = types[0]
	for i, ty in enumerate(types):
		if i == 0:
			continue
		query += " AND "+ty
	return query


def getPids(icd9, src_type=None):
	print >> sys.stderr, 'getting for code '+str(icd9)
	(term_db, stride_db) = getDbs()
	query = "SELECT distinct pid FROM visit WHERE (icd9 like '%%"+icd9+"%%' or icd9=%s)"
	repls = [icd9]
	if src_type:
		srcQuery = srcTypeConditional(src_type)
		query += " AND %s" % srcQuery		
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:		
		result.append(row[0])
	stride_db.close()
	term_db.close()
	return result


if __name__ == "__main__":
	print 'usage: <icd9Codes>'
	pids = []
	for code in sys.argv[1:]:
		pids.extend(getPids(code))
	pids = set(pids)
	for pid in pids:
		print pid






		
