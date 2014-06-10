import sys,os, pprint, json, random, pprint, pickle
from sklearn import cross_validation
from math import sqrt
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from cfier import *
from sklearn.feature_extraction import DictVectorizer as FH
from sklearn.ensemble import RandomForestClassifier as rfc

meta = {
	'termCounting': 'noteboolean',
	'labCounting': 'categorical_status',
	'labCounting2': 'bag',
	'prescriptionCounting': 'bag',
	'codeCounting': 'bag'
}


def predict(testData, ignoreFile, featurefile, diagTerms, featSets, cfierIn, featurizerIn):
	#print 'heres my test data'
	#print testData
	#print 'featurizer file: '+str(featurizerIn)
	ignore = getIgnoreCodes(ignoreFile)
	includeCid=False
	includeLab=False
	includeTerm=False
	includeCode=False
	includePrescription=False	
	if 'labs' in featSets:
		includeLab=True
	if 'meds' in featSets:
		includePrescription=True
	if 'terms' in featSets:
		includeTerm=True
	if 'codes' in featSets:
		includeCode=True
	if 'cids' in featSets:
		includeCid=True
	with open(cfierIn, 'rb') as fi:
		model = pickle.load(fi)
	with open(featurizerIn, 'rb') as fi:
		featurizer = pickle.load(fi)
	testVect = vectorizePids(testData, diagTerms, includeCid=includeCid, includeTerm=includeTerm)	
	#pprint.pprint(testVect)
	testArray = featurizer.transform(testVect).toarray()	
	print 'pid\tprediction'	
	for i, tv in enumerate(testArray):	
		
		l = testData[testData.keys()[i]]
		pred = model.predict(tv)[0]
		print str(testData.keys()[i])+'\t'+str(pred)		
	fimp = featurizer.inverse_transform(model.feature_importances_)	
	writeFeatureImportance(fimp[0], featurefile)


if __name__ == "__main__":
	print >> sys.stderr, 'usage <dataFile> <number of samples> <ignoreFile> <featureOutputFile> <classifierIn> <featurizerIn> labs|meds|terms|cids|codes'	
	data = getFromFile(int(sys.argv[2]), sys.argv[1], 'none')		
	dt = None
	if '-dt' in sys.argv:
		dt = sys.argv[6:]
	testData = {}
	for d,lab in data.iteritems():
		testData[d] = 1

	predict(data, sys.argv[3], sys.argv[4], dt, sys.argv[7:], sys.argv[5], sys.argv[6])
	
	




