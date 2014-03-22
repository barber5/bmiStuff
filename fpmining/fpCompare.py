import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))



def loadFromFile(fileName):
	result = {}
	with open(fileName, 'r') as fi:
		fi.readline()
		while True:
			line = fi.readline()
			if line == '':
				break
			lineArr = line.split('\t')
			nextRes = {
				'freq': lineArr[0],
				'pair': (lineArr[1][1:-1].split(', '), lineArr[2][1:-1].split(', ')),
				'desc': lineArr[3]
			}
	return result



def comparePatterns(caseFile, controlFile):
	cases = loadFromFile(caseFile)
	controls = loadFromFile(controlFile)
	pprint.pprint(cases)

if __name__ == "__main__":
	print 'usage python fpCompare.py <caseFile> <controlFile>'
	comparePatterns(sys.argv[1],sys.argv[2])