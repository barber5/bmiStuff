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

def getCodedVisitsOnly(code, src_type):
	pids = getPids(code, src_type)
	visits = getVisits(pids, src_type)
	for v in visits:
		strv = [str(i) for i in v]
		print '\t'.join(strv)

def getVisits(pids, src_type=None):	
	result = []
	(term_db, stride_db) = getDbs()
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on visits %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, age, timeoffset, year, icd9, src, src_type, duration, cpt FROM visit WHERE pid=%s"
		repls = [int(pid)]
		if src_type:			
			srcQuery = srcTypeConditional(src_type)
			query += " AND %s" % srcQuery
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)		
	return result





if __name__ == "__main__":
	if len(sys.argv) > 2:
		src_type = sys.argv[2:]
	else:
		src_type = None
	getCodedVisitsOnly(sys.argv[1], src_type)	







		
