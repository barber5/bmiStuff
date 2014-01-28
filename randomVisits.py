from patientsForcode import getVisits
from random import random
import sys

def getRandomVisits(num):
	visits = []
	for i in range(num):
		pid = randRange(1, 1257139)
		visits.extend(getVisits([visit]))
	return visits

if __name__ == "__main__":
	visits = getRandomVisits(int(sys.argv[1]))
	for v in visits:
		print v