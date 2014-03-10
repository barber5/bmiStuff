from vecForPatient import getVecForPid
import sys


def getPidsFromFile(fName):
	with open(fName, 'r') as fi:
		firstline = fi.readline()
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split('\t')
			print lineArr
			pid = lineArr[0]
			getVecForPid(pid)

if __name__ == "__main__":
	getPidsFromFile(sys.argv[1])