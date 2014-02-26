import sys,os, pprint, json
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCode import getPids, r, decomp

def expForCode(code):
	pids = r.hget('codes', str(code))
	if not pids:
		pids = getPids(code)
		r.hset('codes', str(code), json.dumps(pids))	
	else:
		pids = json.loads(pids)
	print 'got pids'
	result = {}
	for pid in pids:
		if r.hexists('pats', pid):
			resp = r.hget('pats', pid)
			#print resp
			result[pid] = decomp(resp)
			print >> sys.stderr, pid
		else:
			print >> sys.stderr, 'dont have '+str(pid)

	return result

if __name__ == "__main__":
	expForCode(sys.argv[1])