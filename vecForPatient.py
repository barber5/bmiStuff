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

	

if __name__ == "__main__":
	vec = getPatientVec(sys.argv[1])
	pprint.pprint(vec)