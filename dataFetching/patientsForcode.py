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
		if i%10 == 0:
			print >> sys.stderr, 'working on visits %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, src, src_type, age, timeoffset, year, duration, cpt, icd9 FROM visit WHERE pid=%s"
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
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on notes %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, src, src_type, age, timeoffset, year, duration, cpt, icd9 FROM note where pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)		
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			rowStr = [str(i) for i in row]
			result.append(rowStr)	
	return result

def getPrescriptions(pids, src_type=None):
	result = []
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on prescriptions %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, rxid, src, age, timeoffset, drug_description, route, order_status, ingr_set_id FROM prescription where pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)
	return result

def getLabs(pids):
	result = []
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on labs %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT l.lid, l.src, l.age, l.timeoffset, l.description, l.proc, l.proc_cat, l.line, l.component, l.ord, l.ord_num, l.result_flag, l.ref_low, l.ref_high, l.ref_unit, l.result_inrange, l.ref_norm from lab as l where l.pid=%s"
		repls = [int(pid)]		
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)
	return result

def getFullPatients(code, src_type):
	pids = getPids(code)
	
	visits = getVisits(pids, src_type)
	notes = getNoteIds(pids, src_type)
	prescriptions = getPrescriptions(pids, src_type)
	labs = getLabs(pids)

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
	#getCodedVisitsOnly(sys.argv[1], src_type)
	getFullPatients(sys.argv[1], src_type)








		
