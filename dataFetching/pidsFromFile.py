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


# give this program a file containing pids, one to a line, as well as which line to start and end on (so that you can run several in parallel
# for a large pidfile) and it will select the patient data from the database and cache it in Redis
if __name__ == "__main__":
	print >> sys.stderr, 'usage <pidFile> <startLine> <endLine>'
	getPidsFromFile(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))