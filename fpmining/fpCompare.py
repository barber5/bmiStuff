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
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split('\t')
			pr = (tuple(lineArr[1][1:-1].split(', ')), tuple(lineArr[2][1:-1].split(', ')))
			nextRes = {
				'freq': float(lineArr[0]),				
				'desc': lineArr[3]
			}
			result[pr] = nextRes
	return result



def comparePatterns(caseFile, controlFile):
	cases = loadFromFile(caseFile)
	controls = loadFromFile(controlFile)
	for pr, cs in cases.iteritems():
		if pr not in controls:
			cs['enrichment'] = 0
			other = 0.0
		else:
			cs['enrichment'] = float(cs['freq'] - controls[pr]['freq']) / float(controls[pr]['freq'])
			other = controls[pr]['freq']
		print str(pr[0])+'\t'+str(pr[1])+'\t'+str(cs['enrichment']*100) + '\t'+str(cs['freq'])+'\t'+str(other)+'\t'+str(cs['desc'])


if __name__ == "__main__":
	print >> sys.stderr, 'usage python fpCompare.py <caseFile> <controlFile>'
	comparePatterns(sys.argv[1],sys.argv[2])