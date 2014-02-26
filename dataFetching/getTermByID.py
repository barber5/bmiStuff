from db import *
import sys, pprint


(term_db, stride_db) = getDbs()

def getTerm(term_id):
	print term_id
	query = "SELECT term from terms where termid=%s"
	rows = tryQuery(term_db, query, [term_id])
	print rows


if __name__ == "__main__":
	getTerm(sys.argv[1])