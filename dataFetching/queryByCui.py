from db import *
import sys, pprint, threading, json, os, time, copy, redis, bson
from relatedTerms import *
r = redis.StrictRedis(host='localhost', port=6379, db=0)


import marshal, zlib

MARSHAL_VERSION = 2
COMPRESS_LEVEL = 1
def compIt(res):
	return zlib.compress(marshal.dumps(res, MARSHAL_VERSION), COMPRESS_LEVEL)

def decomp(res):
	return marshal.loads(zlib.decompress(res))

def getCuis(queryTerm, src_type=None):
	(term_db, stride_db) = getDbs()
	query = "SELECT distinct cui,term from terms t1 where t1.term=%s"
	repls = [queryTerm]
	if src_type:
		query += " and src_type=%s"
		repls.append(src_type)	
	rows = tryQuery(term_db, query, repls)
	print >> sys.stderr, 'matching terms: '+str(rows)
	related = set([])
	for r1 in rows:		
		cui = r1[0]
		if not cui:
			continue
		
		terms = closure_term(cui)
		for t in terms:
			related.add(t['cui_exp'])
	terms = set([])
	for rel in related:		
		tidQuery = "SELECT distinct tid,term from terms where cui=%s"
		rows = tryQuery(term_db, tidQuery, [rel])		
		print >> sys.stderr, 'terms: '+str(rows)
		for row in rows:
			terms.add(row[0])
	nids = set([])
	for term in terms:
		nidQuery = "SELECT nid from mgrep where tid=%s"
		rows = tryQuery(stride_db, nidQuery, [term])
		print >> sys.stderr, 'got '+str(len(rows))+' notes for '+str(term)
		for row in rows:
			nids.add(row[0])
	pids = set([])
	for nid in nids:
		pidQuery = "SELECT pid from notes where nid=%s"
		rows = tryQuery(stride_db, pidQuery, [nid])
		for row in rows:
			pids.add(row[0])
	print >> sys.stderr, 'got '+str(len(pids))+ ' pids'
	stride_db.close()
	term_db.close()
	
	#return result


def getSingleVisits(pid, stride_db, src_type=None):	
	query = "SELECT pid, age, timeoffset, year, icd9, src, src_type, duration, cpt FROM visit WHERE pid=%s"
	repls = [int(pid)]
	if src_type:			
		query += " AND src_type=%s"
		repls.append(src_type)
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:
		result.append({
			'pid': row[0],
			'age': row[1],
			'timeoffset': row[2],
			'year': row[3],
			'icd9': row[4],
			'src': row[5],
			'src_type': row[6],
			'duration': row[7],
			'cpt': row[8]
			})	
	return result




def getSingleTerms(nid, stride_db):	
	query = "SELECT m.nid, m.tid, m.negated, m.familyHistory, t.cui, t.termid FROM mgrep as m inner join terminology3.terms as t on m.tid=t.tid where m.nid=%s"
	repls = [int(nid)]	
	rows = tryQuery(stride_db, query, repls)

	result = []
	for row in rows:
		result.append({
			'nid': row[0],
			'tid': row[1],
			'negated': row[2],
			'familyHistory': row[3],			
			'cui': row[4],
			'termid': row[5]	
			})	
	return result


def getSingleNotes(pid, stride_db, src_type=None):	
	query = "SELECT pid, nid, src, src_type, age, timeoffset, year, duration, cpt, icd9 FROM note where pid=%s"
	repls = [int(pid)]
	if src_type:			
		query += " AND src_type=%s"
		repls.append(src_type)		
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:
		terms = getSingleTerms(row[1], stride_db)
		nextNote = {
			'pid': row[0],
			'nid': row[1],
			'src': row[2],
			'src_type': row[3],
			'age': row[4],
			'timeoffset': row[5],
			'year': row[6],
			'duration': row[7],
			'cpt': row[8],
			'icd9': row[9],
			'terms': terms
		}
		result.append(nextNote)	
	return result

def getSinglePrescriptions(pid, stride_db, src_type=None):	
	query = "SELECT pid, rxid, src, age, timeoffset, drug_description, route, order_status, ingr_set_id FROM prescription where pid=%s"		
	repls = [int(pid)]
	if src_type:			
		query += " AND src_type=%s"
		repls.append(src_type)
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:
		result.append({
			'pid': row[0],
			'rxid': row[1],
			'src': row[2],
			'age': row[3],
			'timeoffset': row[4],
			'drug_description': row[5],
			'route': row[6],
			'order_status': row[7],
			'ingr_set_id': row[8]
			})	
	return result

def getSingleLabs(pid, stride_db):	
	query = "SELECT l.lid, l.src, l.age, l.timeoffset, l.description, l.proc, l.proc_cat, l.line, l.component, l.ord, l.ord_num, l.result_flag, l.ref_low, l.ref_high, l.ref_unit, l.result_inrange, l.ref_norm from lab as l where l.pid=%s"
	repls = [int(pid)]		
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:
		result.append({
			'lid': row[0],
			'src': row[1],
			'age': row[2],
			'timeoffset': row[3],
			'description': row[4],
			'proc': row[5],
			'proc_cat': row[6],
			'line': row[7],
			'component': row[8],
			'ord': row[9],
			'ord_num': row[10],
			'result_flag': row[11],
			'ref_low': row[12],
			'ref_high': row[13],
			'ref_unit': row[14],
			'result_inrange': row[15],
			'ref_norm': row[16]
			})				
	return result


count = 0
patList = []
lock = threading.Lock()

def writeSinglePatientFile(pat, pid, code):		    
	pstr = compIt(pat)
	r.hset('pats', pid, pstr)	
	#r.hset('codes', code, pid)
	print 'persisted '+str(pid)
	print 'value length was '+str(len(pstr))
	
	print 'done'*10
	'''fi = open(filePrefix+str(pid)+'.pkl', 'wb')
	pickle.dump(pat, fi)
	fi.close()'''


def getAllSerial(queryTerm, src_type=None):
	pids = None
	if not pids:
		pids = getCuis(queryTerm, src_type)
		pidInt = [int(i) for i in pids]	
		pidInt.sort()	
		pids = [str(s) for s in pidInt]
		#r.hset('cuis', cui, compIt(pids))
	else:
		pids = decomp(pids)
	(term_db, stride_db) = getDbs()
	for i, pid in enumerate(pids):		
		print str(i)+' of '+str(len(pids))
		print pid
		if r.exists(pid):
			print 'exists already'
			continue
		visits = getSingleVisits(pid, stride_db, src_type)		
		print 'got visits'
		notes = getSingleNotes(pid, stride_db, src_type)		
		print 'got notes'
		prescriptions = getSinglePrescriptions(pid, stride_db, src_type)		
		print 'got prescriptions'
		labs = getSingleLabs(pid, stride_db)		
		print 'got labs'
		patient = {
			'pid': pid,
			'src_type': src_type,
			'visits': visits,
			'notes': notes,
			'prescriptions': prescriptions,
			'labs': labs
		}
		print ('persisting '+str(pid)+' ')*10
		writeSinglePatientFile(patient, pid, code)

if __name__ == "__main__":
	if len(sys.argv) == 3:
		src_type = sys.argv[2]
	else:
		src_type = None
	getAllSerial(sys.argv[1], src_type)







		
