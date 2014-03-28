import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from mineConcepts import getFromFile, getRandoms, patientToTimelessConcepts
from conceptPairs import writePairs

def getPairs(num, outFile):
	pats = getRandoms(num)	
	conceptIdx = {}
	pairIdx = {}
	for pid, pat in pats.iteritems():		
		concDict = patientToTimelessConcepts(pat, conceptIdx)
		concs = len(concDict.keys())
		prs = concs*(concs-1)/2
		keyser = concDict.keys()
		print >> sys.stderr, 'working on pid: '+str(pid)+' which has '+str(prs)+' concept pairs'
		for i in range(len(keyser)):
			for j in range(i+1, len(keyser)):
				c1 = keyser[i]
				c2 = keyser[j]
				if c1 < c2:
					t = (c1, c2)
				else:
					t = (c2, c1)								
				if t not in pairIdx:
					pairIdx[t] = []
				pairIdx[t].append(pid)
	print >> sys.stderr, 'done, writing to file...'
	for t, pids in pairIdx.iteritems():
		conce = conceptIdx[t[0][0]] + " + " + conceptIdx[t[1][0]]
		freq = float(len(pids))/float(num)
		if freq > .1:
			print str(freq)+'\t'+str(t[0])+'\t'+str(t[1])+'\t'+conce



if __name__ == "__main__":
	print >> sys.stderr, 'usage python randomPairs.py <number of patient> <outputFile>'
	freq = getPairs(int(sys.argv[1]), sys.argv[2])