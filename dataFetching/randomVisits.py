from vecForPatient import getVecForPid
from queryByCode import r, compIt
from random import randint
import sys, json

def getRandomVisits(num):
	visits = []
	pids = []
	for i in range(num):
		pid = randint(1, 1257139)
		pids.append(pid)
		getVecForPid(pid, 'random')
	r.hset('codes', 'random', compIt(json.dumps(pids)))

if __name__ == "__main__":
	getRandomVisits(int(sys.argv[1]))
	