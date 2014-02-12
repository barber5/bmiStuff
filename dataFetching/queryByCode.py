from db import *
import sys, pprint, threading, pickle, os, time




def getPids(icd9, src_type=None):
	(term_db, stride_db) = getDbs()
	query = "SELECT pid FROM visit WHERE (icd9 like '%%"+icd9+"%%' or icd9=%s)"
	repls = [icd9]
	if src_type:
		query += " and src_type=%s"
		repls.append(src_type)
	print query
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:		
		result.append(row[0])
	return result

def getVisits(pids, src_type=None):
	(term_db, stride_db) = getDbs()
	result = []
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on visits %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, age, timeoffset, year, icd9, src, src_type, duration, cpt FROM visit WHERE pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)		
	return result

def getNoteIds(pids, src_type=None):
	(term_db, stride_db) = getDbs()
	result = []
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on notes %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, nid, src, src_type, age, timeoffset, year, duration, cpt, icd9 FROM note where pid=%s"
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)		
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			rowStr = [str(i) for i in row]
			result.append(rowStr)	
	return result

def getPrescriptions(pids, src_type=None):
	(term_db, stride_db) = getDbs()
	result = []
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on prescriptions %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT pid, rxid, src, age, timeoffset, drug_description, route, order_status, ingr_set_id FROM prescription where pid=%s"		
		repls = [int(pid)]
		if src_type:			
			query += " AND src_type=%s"
			repls.append(src_type)
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)
	return result

def getLabs(pids):
	(term_db, stride_db) = getDbs()
	result = []
	for i, pid in enumerate(pids):
		if i%10 == 0:
			print >> sys.stderr, 'working on labs %s of %s, pid %s' % (i, len(pids), pid)
		query = "SELECT l.lid, l.src, l.age, l.timeoffset, l.description, l.proc, l.proc_cat, l.line, l.component, l.ord, l.ord_num, l.result_flag, l.ref_low, l.ref_high, l.ref_unit, l.result_inrange, l.ref_norm from lab as l where l.pid=%s"
		repls = [int(pid)]		
		rows = tryQuery(stride_db, query, repls)
		for row in rows:	
			result.append(row)
	return result

def getfullNotes(nids):
	(term_db, stride_db) = getDbs()
	result = []
	for i, n in enumerate(nids):
		nid = n[1]		
		print >> sys.stderr, 'working on fullnote %s of %s, nid %s' % (i, len(nids), nid)
		query = "SELECT tid, negated, familyHistory from mgrep where nid=%s"
		rows = tryQuery(stride_db, query, str(nid))
		for row in rows:
			result.append(row)
	return result



def getFullPatients(code, src_type):
	pids = getPids(code, src_type)
	
	visits = getVisits(pids, src_type)
	notes = getNoteIds(pids, src_type)
	prescriptions = getPrescriptions(pids, src_type)
	labs = getLabs(pids)
	result = {
		'visits': visits,
		'notes': notes,
		'prescriptions': prescriptions,
		'labs': labs
	}
	return result
	#getfullNotes(notes)

def getCodedVisitsOnly(code, src_type):
	pids = getPids(code)
	visits = getVisits(pids, src_type)
	for v in visits:
		print '\t'.join(v)


def rowsToFile(rows, fiName):
	fi = open(fiName, 'w')
	for r in rows:
		row = [str(i) for i in r]
		fi.write('\t'.join(row))
		fi.write('\n')
	fi.close()

def patientsToFile(patients, filePrefix):	
	rowsToFile(patients['visits'], filePrefix+'-visits.txt')
	rowsToFile(patients['notes'], filePrefix+'-notes.txt')
	rowsToFile(patients['prescriptions'], filePrefix+'-prescriptions.txt')
	rowsToFile(patients['labs'], filePrefix+'-labs.txt')

class myThread (threading.Thread):
    def __init__(self, name, pids, filePrefix, src_type=None):
		threading.Thread.__init__(self)
		self.name = name
		self.pids = pids
		self.filePrefix = filePrefix
		self.src_type = src_type
        
    def run(self):
		print "Starting " + self.name
		if self.name == 'visits':
			thing = getVisits(self.pids, self.src_type)
		elif self.name == 'notes':
			thing = getNoteIds(self.pids, self.src_type)
		elif self.name == 'prescriptions':
			thing = getPrescriptions(self.pids, self.src_type)
		elif self.name == 'labs':
			thing = getLabs(self.pids)
		else:
			thing = []
		rowsToFile(thing, self.filePrefix+'-'+self.name+'.txt')	
		print 'finished '+self.name	
        

def printAndGetFull(code, src_type, filePrefix):
	pids = getPids(code, src_type)
	print 'initializing threads'
	vt = myThread('visits', pids, filePrefix, src_type)	
	nt = myThread('notes', pids, filePrefix, src_type)	
	pt = myThread('prescriptions', pids, filePrefix, src_type)	
	lt = myThread('labs', pids, filePrefix, src_type)	
	print 'threads initialized'
	vt.start()
	nt.start()
	pt.start()
	lt.start()	
	print 'done done done'

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
	query = "SELECT m.nid, m.tid, m.negated, m.familyHistory, t.term, t.ontology, t.cui, t.termid FROM mgrep as m inner join terminology3.terms as t on m.tid=t.tid where m.nid=%s"
	repls = [int(nid)]	
	rows = tryQuery(stride_db, query, repls)

	result = []
	for row in rows:
		result.append({
			'nid': row[0],
			'tid': row[1],
			'negated': row[2],
			'familyHistory': row[3],
			'term': row[4],
			'ontology': row[5],
			'cui': row[6],
			'termid': row[7]	
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

def writeSinglePatientFile(pat, pid, filePrefix):
	fi = open(filePrefix+pid+'.txt', 'w')
	fi.write(pat.__repr__())
	fi.close()
	fi = open(filePrefix+pid+'.pkl', 'wb')
	pickle.dump(pat, fi)
	fi.close()


class patientThread(threading.Thread):
	def __init__(self, pidd, filePrefix, stride_db, src_type=None):		   
		self.pid = str(pidd)
		self.filePrefix = filePrefix
		self.src_type = src_type
		self.stride_db = stride_db
		threading.Thread.__init__(self)     
        
	def run(self):		
		visits = getSingleVisits(self.pid, self.stride_db, self.src_type)		
		notes = getSingleNotes(self.pid, self.stride_db, self.src_type)		
		prescriptions = getSinglePrescriptions(self.pid, self.stride_db, self.src_type)		
		labs = getSingleLabs(self.pid, self.stride_db)		
		patient = {
			'pid': self.pid,
			'src_type': self.src_type,
			'visits': visits,
			'notes': notes,
			'prescriptions': prescriptions,
			'labs': labs
		}
		self.stride_db.close()
		writeSinglePatientFile(patient, self.pid, self.filePrefix)

		


def parallelPatients(code, src_type, filePrefix):
	pids = getPids(code, src_type)	
	for i, pid in enumerate(pids):
		print 'working on '+str(pid)
		print 'which is '+str(i)+' of '+str(len(pids))		
		if os.path.isfile(filePrefix+str(pid)+'.pkl'):
			continue		
		try:
			(term_db, stride_db) = getDbs()
			term_db.close()
		except Exception as e:
			time.sleep(.1)
		pt = patientThread(pid, filePrefix, stride_db, src_type)		
		pt.start()


if __name__ == "__main__":
	if len(sys.argv) > 3:
		src_type = sys.argv[3]
	else:
		src_type = None
	#getCodedVisitsOnly(sys.argv[1], src_type)
	#patients = getFullPatients(sys.argv[1], src_type)
	#patientsToFile(patients, sys.argv[2])
	#printAndGetFull(sys.argv[1], src_type, sys.argv[2])
	parallelPatients(sys.argv[1], src_type, sys.argv[2])








		
