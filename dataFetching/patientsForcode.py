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
	for pid in pids:
		query = "SELECT pid, age, timeoffset, year, icd9 FROM visit WHERE pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			line = ''
			for r in row:
				line += str(r)+'\t'
			line = line[:-1]
			result.append(line)					
	return result

def getNoteIds(pids):
	result = []
	for pid in pids:
		query = "SELECT pid, patient, nid, src, src_type, age, timeoffset, year, duration, cpt, icd9 FROM notes where pid=%s"
		rows = tryQuery(stride_db, query, [int(pid)])
		for row in rows:	
			line = ''
			for r in row:
				line += str(r)+'\t'
			line = line[:-1]
			result.append(line)					
	return result

if __name__ == "__main__":
	pids = getPids(sys.argv[1])
	print pids
	if len(sys.argv) > 2:
		visits = getVisits(pids, sys.argv[2])
	else:
		visits = getVisits(pids)
	for v in visits:
		print v
