from relatedTerms import *
from db import *
import sys,pprint
(term_db, stride_db) = getDbs()

def getPatientVec(pid):
	query = "SELECT n.nid, n.timeoffset, m.tid FROM note as n inner join mgrep as m on n.nid=m.nid WHERE n.pid=%s"
	rows = tryQuery(stride_db, query, [pid])
	notes = {}
	for row in rows:
		nid = row[0]
		if nid not in notes:
			notes[nid] = {
				'nid': nid,
				'offset': row[1],
				'terms': []
			}
		notes[nid]['terms'].append(row[2])
	return {
		'pid': pid,
		'notes': notes.values()
	}

def getMultiplePatientVec(pids):
	result = []
	for pid in pids:
		result.append(getPatientVec(pid))
		print pid
	return result

if __name__ == "__main__":
	if len(sys.argv) == 2
		vec = getPatientVec(sys.argv[1])
	elif len(sys.argv) > 2:
		vec = getMultiplePatientVec(sys.argv[1:])
	pprint.pprint(vec)	