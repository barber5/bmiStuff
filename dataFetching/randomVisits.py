from vecForPatient import getVecForPid
from random import randint
import sys

def getRandomVisits(num):
	visits = []
	for i in range(num):
		pid = randint(1, 1257139)
		visits.extend(getVecForPid(pid))
	return visits

if __name__ == "__main__":
	visits = getRandomVisits(int(sys.argv[1]))
	for v in visits:
		print v