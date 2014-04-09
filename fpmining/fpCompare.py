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
	goodOnes = {}
	i = 0
	for pr, cs in cases.iteritems():
		i+=1
		if i%1000==0:
			print >> sys.stderr, str(i)+' of '+str(len(cases))
		if pr not in controls:
			cs['enrichment'] = 99999
			cs['other'] = 0.0
			other = 0.0
		else:
			cs['enrichment'] = 100*float(cs['freq'] - controls[pr]['freq']) / float(controls[pr]['freq'])
			other = controls[pr]['freq']
			cs['other'] = other
			
			if cs['enrichment'] > 10:
				goodOnes[pr] = cs
	return goodOnes

def writeToFile(sig, outFile):
	with open(outFile, 'w') as fi:
		for pr, cs in sig.iteritems():
			fi.write(str(pr[0])+'\t'+str(pr[1])+'\t'+str(cs['enrichment'])+'\t'+str(cs['freq'])+'\t'+str(cs['other'])+'\t'+str(cs['desc']))
			fi.write('\n')

if __name__ == "__main__":
	print >> sys.stderr, 'usage python fpCompare.py <caseFile> <controlFile> <outputFile>'
	sig = comparePatterns(sys.argv[1],sys.argv[2])
	writeToFile(sig, sys.argv[3])


