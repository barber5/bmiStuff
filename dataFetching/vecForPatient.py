from queryByCode import getSingleVisits, getSingleVisits, getSinglePrescriptions, getSingleLabs, writeSinglePatientFile

def getVecForPid(pid):
	(term_db, stride_db) = getDbs()
	if r.exists(pid):
		print 'exists already'
		return
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
	writeSinglePatientFile(patient, pid)



if __name__ == "__main__":	
	getAllSerial(sys.argv[1])