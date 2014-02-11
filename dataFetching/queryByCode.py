from db import *
import sys, pprint, threading


(term_db, stride_db) = getDbs()

def getPids(icd9, src_type=None):
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
    def __init__(self, threadID, name, counter):

        threading.Thread.__init__(self)
        self.threadID = threadID
        self.counter = counter
        self.name = name
        
    def run(self, pids, filePrefix, src_type=None):
		print "Starting " + self.name
		if self.name == 'visits':
			thing = getVisits(pids, src_type)
		elif self.name == 'notes':
			thing = getNoteIds(pids, src_type)
		elif self.name == 'prescriptions':
			thing = getPrescriptions(pids, src_type)
		elif self.name == 'labs':
			thing = getLabs(pids)

		else:
			thing = []
		rowsToFile(thing, filePrefix+'-'+self.name+'.txt')	
		print 'finished '+self.name	
        

def printAndGetFull(code, src_type, filePrefix):
	pids = getPids(code, src_type)
	print 'initializing threads'
	vt = myThread(1, 'visits', 1)
	
	nt = myThread(2, 'notes', 2)
	
	pt = myThread(3, 'prescriptions', 3)
	
	lt = myThread(4, 'labs', 4)
	
	print 'threads initialized'
	vt.start(pids, filePrefix, src_type)
	nt.start(pids, filePrefix, src_type)
	pt.start(pids, filePrefix, src_type)
	lt.start(pids, filePrefix, src_type)

	
	print 'done done done'

if __name__ == "__main__":
	if len(sys.argv) > 3:
		src_type = sys.argv[3]
	else:
		src_type = None
	#getCodedVisitsOnly(sys.argv[1], src_type)
	#patients = getFullPatients(sys.argv[1], src_type)
	#patientsToFile(patients, sys.argv[2])
	printAndGetFull(sys.argv[1], src_type, sys.argv[2])








		
