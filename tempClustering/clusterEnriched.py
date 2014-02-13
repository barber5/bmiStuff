import sys, os, re, pprint
sys.path.append(os.path.realpath('../posteriors'))
sys.path.append(os.path.realpath('./posteriors'))
from readIcd9Patients import getInput, binConditionsByAge, selectByAge, binnedTransform, binnedWithCodes, loadCodes, filterCodes
from codeEnrichment import getEnrichments
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import KernelPCA
from sklearn.cluster import DBSCAN as cluster
from sklearn import preprocessing



def doClustering(codeFile, patientFile, randomFile, minAge, maxAge, patientSample, randomSample, freqThreshold, enrichThreshold):
	(enrichments, data) = getEnrichments(codeFile, patientFile, randomFile, minAge, maxAge, freqThreshold, patientSample, randomSample)	
	filteredPat = filterCodes(data['xformedPat'], lambda x: x in enrichments)
	filteredPat.update(data['xformedRnd'])
	codes = data['codes']
	patientFeatures = {}
	measurements = []
	pidIndexer = {}
	i=0
	for patient, conds in filteredPat.iteritems():			
		patientDict = {}
		for cond in conds:			
			patientDict[str(cond)] = 1
		pidIndexer[i] = patient
		measurements.append(patientDict)
		i += 1
	vec = DictVectorizer()
	featArray = vec.fit_transform(measurements).toarray()	
	#featArray = preprocessing.scale(featArray)
	print >> sys.stderr, 'got features'
	tfidf = TfidfTransformer()
	tfidfArray = tfidf.fit_transform(featArray)
	print >> sys.stderr, 'got tfidf'
	dimReducer = KernelPCA(n_components=300)
	reducedFeatArray = dimReducer.fit_transform(tfidfArray)
	print >> sys.stderr, "reduced dimensions"
	#reducedFeatArray = featArray
	c = cluster(metric='correlation', algorithm='brute', min_samples=10, eps=.2)
	labels = c.fit_predict(reducedFeatArray)	
	print >> sys.stderr, 'clustering finished'
	clusters = {}
	clusterPatients = {}
	for i, l in enumerate(labels):
		if l == -1:
			continue
		if l not in clusters:
			clusters[l] = []
			clusterPatients[l] = []
		clusters[l].append(i)
		pid = pidIndexer[i]
		condDicts = filteredPat[pid]
		clpat = {
			'pid': pid,
			'conditions': [(i, codes[i]) for i in condDicts]
		}
		clusterPatients[l].append(clpat)
	return clusterPatients

def writeClusters(clu, fileName):
	fi = open(fileName, 'w')
	for clid, patients in clu.iteritems():
		for pat in patients:
			fi.write('{}\t{}\n'.format(pat['pid'], clid))
	fi.close()

if __name__ == "__main__":
	if len(sys.argv) != 11:
		print >> sys.stderr, 'usage: python {} {} {} {} {} {} {} {} {} {} {}'.format(sys.argv[0], 'icd9codefile', 'conditionVisits', 'randomVisits', 'minAge', 'maxAge', 'patientSampleRate', 'randomSampleRate', 'freqRequired', 'enrichmentThreshold', 'outputFile')
		sys.exit(0)
	clu = doClustering(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8]), float(sys.argv[9]))
	writeClusters(clu, sys.argv[10])
	pprint.pprint(clu)
	