import sys,os, pprint, json
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCode import getPids, r

def expForCode(code):
	pids = getPids(code)
	result = {}
	for pid in pids:
		if r.exists(pid):
			result[pid] = json.loads(r.get(pid))
			print >> sys.stderr, pid
			
	return result

if __name__ == "__main__":
	expForCode(sys.argv[1])