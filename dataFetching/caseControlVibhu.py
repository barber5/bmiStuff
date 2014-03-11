from vecForPatient import getVecForPid
import sys


def getPidsFromFile(fName, lo, hi):
	i = 0
	with open(fName, 'r') as fi:
		firstline = fi.readline()
		while True:
			i += 1
			if i < lo:
				continue
			if i > hi:
				break
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split(' ')
			print lineArr
			pid = lineArr[1]
			getVecForPid(pid)
			pid = lineArr[2]
			getVecForPid(pid)



if __name__ == "__main__":
	getPidsFromFile(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))