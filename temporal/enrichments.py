import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
sys.path.append(os.path.realpath('../fpmining'))
sys.path.append(os.path.realpath('./fpmining'))

from queryByCui import r, decomp, compIt

def getRandoms(num):
	res = r.hget('codes', 'random')
	li = json.loads(decomp(res))
	result = {}
	while len(result) < num:
		next = str(random.choice(li))
		result[next] = 0
	return result

def getFromFile(num, fileName, rndSrc):
	pids = {}
	result = {}
	with open(fileName, 'r') as fi:
		fi.readline()
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split(' ')
			#print lineArr
			pidNeg = lineArr[2]
			pidPos = lineArr[1]
			pids[pidNeg] = 0
			pids[pidPos] = 1
	pidKeys = pids.keys()
	while len(result) < num/2:
		next = random.choice(pidKeys)
		if pids[next] != 1:
			continue
		resp = r.hget('pats', str(next))
		if not resp:
			continue
		result[next] = 1
	if rndSrc == 'file':
		while len(result) < num:
			next = random.choice(pidKeys)
			if pids[next] != 0:
				continue
			resp = r.hget('pats', str(next))
			if not resp:
				continue
			result[next] = 0
	else:
		rnds = getRandoms(num/2)
		for rn in rnds:
			result[rn] = 0
	return result


def getEnrichments(data):
	for p in data:
		pprint.pprint(p)


if __name__ == "__main__":		
	print >> sys.stderr, 'usage: <patientFile> <dataSetSize>'		
	rndSrc = 'cache'

	data = getFromFile(int(sys.argv[2]), sys.argv[1], rndSrc)		
	

	