from vecForPatient import getVecForPid
import sys


def getPidsFromFile(fName, lo, hi):
	i = 0
	lines = []
	with open(fName, 'r') as fi:
		firstline = fi.readline()

		while True:			
			line = fi.readline().strip()
			if line == '':
				break
			lines.append(line)
		

	for i in range(lo-1, hi+1):
		line = lines[i]				
		pid = line
		getVecForPid(pid)
		#pid = lineArr[2]		



if __name__ == "__main__":
	getPidsFromFile(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))