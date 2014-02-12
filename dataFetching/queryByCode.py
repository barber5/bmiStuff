from db import *
import sys, pprint, threading, pickle, os




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

def getSingleVisits(pid, src_type=None):
	(term_db, stride_db) = getDbs()
	query = "SELECT pid, age, timeoffset, year, icd9, src, src_type, duration, cpt FROM visit WHERE pid=%s"
	repls = [int(pid)]
	if src_type:			
		query += " AND src_type=%s"
		repls.append(src_type)
	rows = tryQuery(stride_db, query, repls)
	return rows

def getSingleNotes(pid, src_type=None):
	(term_db, stride_db) = getDbs()
	query = "SELECT pid, nid, src, src_type, age, timeoffset, year, duration, cpt, icd9 FROM note where pid=%s"
	repls = [int(pid)]
	if src_type:			
		query += " AND src_type=%s"
		repls.append(src_type)		
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:	
		rowStr = [str(i) for i in row]
		result.append(rowStr)
	return result

def getSinglePrescriptions(pid, src_type=None):
	(term_db, stride_db) = getDbs()
	query = "SELECT pid, rxid, src, age, timeoffset, drug_description, route, order_status, ingr_set_id FROM prescription where pid=%s"		
	repls = [int(pid)]
	if src_type:			
		query += " AND src_type=%s"
		repls.append(src_type)
	rows = tryQuery(stride_db, query, repls)
	return rows

def getSingleLabs(pid):
	(term_db, stride_db) = getDbs()
	query = "SELECT l.lid, l.src, l.age, l.timeoffset, l.description, l.proc, l.proc_cat, l.line, l.component, l.ord, l.ord_num, l.result_flag, l.ref_low, l.ref_high, l.ref_unit, l.result_inrange, l.ref_norm from lab as l where l.pid=%s"
	repls = [int(pid)]		
	rows = tryQuery(stride_db, query, repls)
	return rows

def writeSinglePatientFile(pat, pid, filePrefix):
	fi = open(filePrefix+pid+'.txt', 'w')
	fi.write(pat.__repr__())
	fi.close()
	fi = open(filePrefix+pid+'.pkl', 'wb')
	pickle.dump(pat, fi)
	fi.close()


class patientThread(threading.Thread):
	def __init__(self, pidd, filePrefix, src_type=None):		   
		self.pid = str(pidd)
		self.filePrefix = filePrefix
		self.src_type = src_type
		threading.Thread.__init__(self)     
        
	def run(self):		
		visits = getSingleVisits(self.pid, self.src_type)		
		notes = getSingleNotes(self.pid, self.src_type)		
		prescriptions = getSinglePrescriptions(self.pid, self.src_type)		
		labs = getSingleLabs(self.pid)		
		patient = {
			'pid': self.pid,
			'src_type': self.src_type,
			'visits': visits,
			'notes': notes,
			'prescriptions': prescriptions,
			'labs': labs
		}
		writeSinglePatientFile(patient, self.pid, self.filePrefix)
		


def parallelPatients(code, src_type, filePrefix):
	pids = getPids(code, src_type)
	for i, pid in enumerate(pids):
		if os.path.isfile(filePrefix+str(pid)+'.pkl'):
			continue
		print 'working on '+str(pid)
		print 'which is '+str(i)+' of '+str(len(pids))
		pt = patientThread(pid, filePrefix, src_type)
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








		
