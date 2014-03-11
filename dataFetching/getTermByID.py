from db import *
import sys, pprint


(term_db, stride_db) = getDbs()

def getTerm(term_id):		
	query = "SELECT term from terms where tid=%s"
	rows = tryQuery(term_db, query, [term_id])
	return rows[0][0].upper()

def getLab(component):
	query = "SELECT name from component where component=%s"
	rows = tryQuery(stride_db, query, [component])
	return rows[0][0].upper()	

def getIngredient(rxcui):
	query = "SELECT ingredient from ingredient where rxcui=%s"
	rows = tryQuery(stride_db, query, [rxcui])
	return rows[0][0].upper()		

def getTermCui(cui):
	#print >> sys.stderr, 'cui: '+str(cui)
	query = "SELECT cid from str2cid where cui=%s"
	rows = tryQuery(term_db, query, [cui])
	if len(rows) == 0:
		return None
	if len(rows[0]) == 0:
		return None
	if not rows[0][0]:
		return None
	return rows[0][0]

def getConcept(cid):
	query = "SELECT str from str2cid where cid=%s"
	rows = tryQuery(term_db, query, [cid])
	if len(rows) == 0:
		return None
	if len(rows[0]) == 0:
		return None
	if not rows[0][0]:
		return None
	return rows[0][0]

def getIngredients(ingr_set_id):
	query = "SELECT rxcui from ingredient where ingr_set_id=%s"
	rows = tryQuery(stride_db, query, [ingr_set_id])
	ingredients = []
	for row in rows:
		ingredients.append(row[0])
	return ingredients

if __name__ == "__main__":
	getTerm(sys.argv[1])