from db import *
import sys, pprint, threading, json, os, time, copy, redis, bson
r = redis.StrictRedis(host='localhost', port=6379, db=0)


import marshal, zlib

MARSHAL_VERSION = 2
COMPRESS_LEVEL = 1
def compIt(res):
	return zlib.compress(marshal.dumps(res, MARSHAL_VERSION), COMPRESS_LEVEL)

def decomp(res):
	return zlib.decompress(marshal.loads(res))

def getPids(icd9, src_type=None):
	(term_db, stride_db) = getDbs()
	query = "SELECT distinct pid FROM visit WHERE (icd9 like '%%"+icd9+"%%' or icd9=%s)"
	repls = [icd9]
	if src_type:
		query += " and src_type=%s"
		repls.append(src_type)	
	rows = tryQuery(stride_db, query, repls)
	result = []
	for row in rows:		
		result.append(row[0])
	stride_db.close()
	term_db.close()
	return result

def getVisits(pids, src_type=None):	
	result = []
	(term_db, stride_db) = getDbs()
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
		strv = [str(i) for i in v]
		print '\t'.join(strv)


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
	r.hset('codes', code, pid)
	print 'persisted '+str(pid)
	print 'value length was '+str(len(pstr))
	
	print 'done'*10
	'''fi = open(filePrefix+str(pid)+'.pkl', 'wb')
	pickle.dump(pat, fi)
	fi.close()'''


class patientThread(threading.Thread):
	def __init__(self, pidd, filePrefix, stride_db, src_type=None):		   
		self.pid = str(pidd)
		self.filePrefix = filePrefix
		self.src_type = src_type
		self.stride_db = stride_db
		threading.Thread.__init__(self)    

        
	def run(self):		
		global count
		global patList
		print 'attempting to acquire lock'
		lock.acquire()
		print 'acquired lock'		
		count += 1
		print 'incrementing: count is '+str(count)	
		print 'releasing lock'	
		lock.release()
		print 'released lock'
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
		print 'finished '+str(self.pid)
		print 'attempting to acquire lock'
		lock.acquire()
		print 'got lock'
		count -= 1
		patList.append(patient)
		print 'decrementing: count is '+str(count)	
		print 'releasing lock'	
		lock.release()
		print 'releasing lock'
		self.stride_db.close()
		print ('persisting '+self.pid+'\n')*100
		writeSinglePatientFile(patient, self.pid, self.filePrefix)
		

def writeResults(code, filePrefix):
	print 'writing results'*20
	global patList
	
	print 'attempting to acquire lock'
	lock.acquire()
	print 'lock acquired'
	dl = []
	for i, p in enumerate(patList):
		print 'copying '+str(i)
		pc = copy.deepcopy(p)
		print 'done'
		dl.append(pc)	
	print 'attempting to release lock'
	lock.release()
	print 'lock released'	
	fi = open(filePrefix+str(code)+'.json', 'w')
	fi.write(json.dumps(dl))
	print 'dumped'*20
	fi.close()


def parallelPatients(code, src_type, filePrefix, minpid):
	pids = getPids(code, src_type)
	pidInt = [int(i) for i in pids]	
	pidInt.sort()	
	pids = [str(s) for s in pidInt]
	
	for i, pid in enumerate(pids):
		global count
		global patList
		cnt = 0
		print 'attempting to acquire lock'
		lock.acquire()
		print 'lock acquired'
		cnt = count
		print 'releasing lock'
		lock.release()
		print 'lock released'
		while cnt > 50:					
			print 'too many threads'
			print str(cnt) + 'total threads'
			time.sleep(5)	
			print 'attempting to acquire lock'		
			lock.acquire()
			print 'lock acquired'
			cnt = count
			print 'attempting to release lock'
			lock.release()
			print 'lock released'
			print 'awake'
		print filePrefix+str(pid)+'.txt'	
		
		

		if int(pid) < minpid:
			print 'skipping'
			continue		
		if os.path.isfile(filePrefix+str(pid)+'.txt'):			
			continue							
		else:
			print 'not exists'						
			print filePrefix+str(pid)+'.txt'
		#print 'working on '+str(pid)
		#print 'which is '+str(i)+' of '+str(len(pids))		
		#print 'grabbing connections'
		(term_db, stride_db) = getDbs()
		term_db.close()				
		pt = patientThread(pid, filePrefix, stride_db, src_type)				
		pt.start()		
	for thr in threading.enumerate():
		t.join()
	writeResults(code, filePrefix)


def getAllSerial(code, src_type=None):
	pids = r.hget('codes', code)
	if not pids:
		pids = getPids(code, src_type)
		pidInt = [int(i) for i in pids]	
		pidInt.sort()	
		pids = [str(s) for s in pidInt]
		r.hset('codes', code, compIt(pids))
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







		
