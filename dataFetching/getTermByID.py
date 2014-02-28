from db import *
import sys, pprint


(term_db, stride_db) = getDbs()

def getTerm(term_id):	
	query = "SELECT term from terms where termid=%s"
	rows = tryQuery(term_db, query, [term_id])
	return rows[0][0]

def getTermCui(cui):
	print >> sys.stderr, 'cui: '+str(cui)
	query = "SELECT str from str2cid where cui=%s"
	rows = tryQuery(term_db, query, [cui])
	return rows[0][0]

if __name__ == "__main__":
	getTerm(sys.argv[1])