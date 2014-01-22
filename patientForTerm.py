from relatedTerms import *
from db import *
import sys,pprint
(term_db, stride_db) = getDbs()

def getPatientsForTerms(terms):
	patients = {}
	for t in terms:
		term = t['tid']
		query = "SELECT n.pid from mgrep as m inner join note as n on m.nid=n.nid  WHERE m.tid=%s group by n.pid"
		rows = tryQuery(stride_db, query, [term])
		for row in rows:			
			pid = row[0]
			if pid not in patients:
				patients[pid] = []
			patients[pid].append(t['term'])
	return patients

if __name__ == "__main__":
	terms = related_terms(sys.argv[1])
	patients = getPatientsForTerms(terms)
	pprint.pprint(patients.keys())