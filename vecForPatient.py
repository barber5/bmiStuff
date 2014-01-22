from relatedTerms import *
from db import *
import sys,pprint
(term_db, stride_db) = getDbs()

def getPatientVec(pid):
	query = "SELECT * FROM note as n inner join mgrep as m on n.nid=m.nid WHERE n.pid=%s AND m.tid > 0"
	rows = tryQuery(stride_db, query, [pid])
	print rows[0]

if __name__ == "__main__":
	getPatientVec(sys.argv[1])