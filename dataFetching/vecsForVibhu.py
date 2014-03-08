from vecForPatient import getVecForPid
import sys


def getPidsFromFile(fName):
	with open(fName, 'r') as fi:
		while True:
			line = fi.readline()
			if line == '':
				break
			lineArr = line.split(' ')
			pid = lineArr[2]
			getVecForPid(pid)

if __name__ == "__main__":
	getPidsFromFile(sys.argv[1])