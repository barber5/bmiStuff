import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from mineConcepts import getFromFile, getRandoms, patientToTimelessConcepts




def writePairs(num, pairIdx, outFile):
	with open(outFile, 'w') as fi:
		fi.write(num)
		fi.write('\n')
		for pr, idx in pairIdx.iteritems():
			idxStr = [str(i) for i in idx]
			fi.write(str(pr[0])+','+str(pr[1])+'\t'+','.join(idxStr))
			fi.write('\n')


def getPairs(num, patientFile, outFile):
	pats = getFromFile(num, patientFile)	
	conceptIdx = {}
	pairIdx = {}
	for pid, pat in pats.iteritems():
		concDict = patientToTimelessConcepts(pat, conceptIdx)
		for i in range(len(concDict.keys())):
			for j in range(i+1, len(concDict.keys())):
				c1 = concDict.keys()[i]
				c2 = concDict.keys()[j]
				l = [c1, c2]
				l = sorted(l)
				t = tuple(l)
				if t not in pairIdx:
					pairIdx[t] = []
				pairIdx[t].append(pid)
	writePairs(pairIdx, outFile)



if __name__ == "__main__":
	print 'usage python conceptPairs.py <number of patient> <patientFile> <outputFile>'
	freq = getPairs(int(sys.argv[1]), sys.argv[2], sys.argv[3])