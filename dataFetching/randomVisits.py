from vecForPatient import getVecForPid
from random import randint
import sys

def getRandomVisits(num):
	visits = []
	for i in range(num):
		pid = randint(1, 1257139)
		getVecForPid(pid, 'random')
	

if __name__ == "__main__":
	getRandomVisits(int(sys.argv[1]))
	