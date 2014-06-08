import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCui import r, decomp, compIt
from vecForPatient import getVecForPid



def getPatient(pid, cacheOnly=False):
	# try to get patient, if cacheOnly return one, if not cacheOnly, get it from the db
	pat = r.hget('pats', str(pid))
	if not pat and cacheOnly:
		return None
	elif not pat:
		getVecForPid(pid)
		return getPatient(pid, cacheOnly=True)
	else:
		return decomp(pat)

def getPatsForCode(code):
	li = r.hget('codes', code)
	if not li:
		return None
	else:
		return json.loads(decomp(li))

	
# get the list of patients in the cache having a given code or fetch a patient from the cache by pid
if __name__ == "__main__":	
	if '-c' in sys.argv:
		print getPatsForCode(sys.argv[-1])
	elif '-p' in sys.argv:
		pprint.pprint(getPatient(sys.argv[-1], cacheOnly=True))
	else:
		print 'usage is python getPatient.py -c <code>|-p <pid>'
