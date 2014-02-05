from db import *
import sys, pprint


(term_db, stride_db) = getDbs()

def getPids(icd9):
	query = "SELECT pid FROM visit WHERE icd9 like '%%"+icd9+"%%' or icd9=%s"
	rows = tryQuery(stride_db, query, [icd9])
	result = []
	for row in rows:		
		result.append(row[0])
	return result

def getVisits(pids, src_type=None):
	result = []
	for i, pid in enumerate(pids):
		print i
		print pid
		print len(pids)
		print >> sys.stderr, 'working on visit %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, age, timeoffset, year, icd9 FROM visit WHERE pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)		
	return result

def getNoteIds(pids, src_type=None):
	result = []
	for pid in pids:
		print >> sys.stderr, 'working on note {} of {} (pid: {})'.format(i, len(pids), pid)
		query = "SELECT pid, nid, src, src_type, age, timeoffset, year, duration, cpt, icd9 FROM note where pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)		
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)	
	return result

def getPrescriptions(pids, src_type=None):
	result = []
	for pid in pids:
		print >> sys.stderr, 'working on prescription {} of {} (pid: {})'.format(i, len(pids), pid)
		query = "SELECT pid, rxid, src, age, offset,  where pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)
	return result

def getFullPatients(code, src_type):
	pids = getPids(code)
	
	visits = getVisits(pids, src_type)
	notes = getNoteIds(pids, src_type)
	prescriptions = getPrescriptions(pids, src_type)

def getCodedVisitsOnly(code, src_type):
	pids = getPids(code)
	visits = getVisits(pids, src_type)
	for v in visits:
		print '\t'.join(v)

if __name__ == "__main__":
	if len(sys.argv) > 2:
		src_type = sys.argv[2]
	else:
		src_type = None
	getCodedVisitsOnly(sys.argv[1], src_type)








		
