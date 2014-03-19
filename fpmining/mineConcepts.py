import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from getPatient import getPatient, getPatsForCode



def getFromFile(num, fileName):
	pids = {}
	result = {}
	with open(fileName, 'r') as fi:
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split(' ')
			#print lineArr
			if len(lineArr) > 2:
				pidNeg = lineArr[2]
				pids[pidNeg] = 0
			pidPos = lineArr[1]			
			pids[pidPos] = 1
	pidKeys = pids.keys()
	while len(result) < num:
		next = random.choice(pidKeys)
		print 'grabbing pid: '+str(next)
		if pids[next] != 1:
			continue
		resp = getPatient(next)
		if not resp:
			continue
		result[next] = 1	
	return result

def getRandoms(num):
	li = getPatsForCode('random')
	result = {}
	while len(result) < num:
		next = str(random.choice(li))
		result[next] = 0
	return result

def patientToTimelessConcepts(patient):
	None




if __name__ == "__main__":
	getFromFile(int(sys.argv[1]), sys.argv[2])










