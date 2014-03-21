import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from mineConcepts import getFromFile, getRandoms, patientToTimelessConcepts


def writePairs(num, pairIdx, outFile):
	with open(outFile, 'w') as fi:
		fi.write(str(num))
		fi.write('\n')
		for pr, idx in pairIdx.iteritems():
			if float(len(idx))/float(num) < .2:
				continue
			idxStr = [str(i) for i in idx]			
			fi.write(str(pr[0])+'\t'+str(pr[1])+'\t'+','.join(idxStr))
			fi.write('\n')


def getPairs(num, patientFile, outFile):
	pats = getFromFile(num, patientFile)	
	conceptIdx = {}
	pairIdx = {}
	for pid, pat in pats.iteritems():		
		concDict = patientToTimelessConcepts(pat, conceptIdx)
		concs = len(concDict.keys())
		prs = concs*(concs-1)/2
		print >> sys.stderr, 'working on pid: '+str(pid)+' which has '+str(prs)+' concept pairs'
		for i,c1 in enumerate(concDict.keys()):
			for j,c2 in enumerate(concDict.keys()):						
				if j <= i:
					continue
				if c1 < c2:
					t = (c1, c2)
				else:
					t = (c2, c1)								
				if t not in pairIdx:
					pairIdx[t] = []
				pairIdx[t].append(pid)
	print >> sys.stderr, 'done, writing to file...'
	writePairs(num, pairIdx, outFile)



if __name__ == "__main__":
	print 'usage python conceptPairs.py <number of patient> <patientFile> <outputFile>'
	freq = getPairs(int(sys.argv[1]), sys.argv[2], sys.argv[3])