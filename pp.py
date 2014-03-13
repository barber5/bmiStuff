import sys

def getPredPowers(fileName):
	with open(fileName, 'r') as fi:
		while True:
			line = fi.readline()
			if line == '':
				break
			lineArr = line.split('\t')
			print lineArr

if __name__ == "__main__":
	getPredPowers(sys.argv[1])