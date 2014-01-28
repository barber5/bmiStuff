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

def getVisits(pids):
	result = []
	for pid in pids:
		query = "SELECT * FROM visit WHERE pid=%s";
		rows = tryQuery(stride_db, query, [pid])
		for row in rows:	
			print row	
			result.append(row)		
	return result

if __name__ == "__main__":
	pids = getPids(sys.argv[1])
	visits = getVisits(pids)
