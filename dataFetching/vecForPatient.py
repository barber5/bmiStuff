from queryByCode import getSingleVisits, getSingleVisits,getSingleNotes, getSinglePrescriptions, getSingleLabs, writeSinglePatientFile, r
import sys
from db import *


def getVecForPid(pid, code=None):
	(term_db, stride_db) = getDbs()
	if r.hexists('pats',pid):
		print >> sys.stderr, 'exists already'
		return
	visits = getSingleVisits(pid, stride_db, None)		
	print >> sys.stderr, 'got visits'
	notes = getSingleNotes(pid, stride_db, term_db, None)		
	print >> sys.stderr, 'got notes'
	prescriptions = getSinglePrescriptions(pid, stride_db, None)		
	print >> sys.stderr, 'got prescriptions'
	labs = getSingleLabs(pid, stride_db)		
	print >> sys.stderr, 'got labs'
	patient = {
		'pid': pid,
		'src_type': None,
		'visits': visits,
		'notes': notes,
		'prescriptions': prescriptions,
		'labs': labs
	}
	print >> sys.stderr, ('persisting '+str(pid)+' ')*10
	writeSinglePatientFile(patient, pid, code)



if __name__ == "__main__":	
	getVecForPid(sys.argv[1])