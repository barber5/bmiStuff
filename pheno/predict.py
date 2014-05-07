import sys,os, pprint, json, random, pprint, pickle
from sklearn import cross_validation
from math import sqrt
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from cfier import vectorizePids, getFromFile, getIgnoreCodes
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
	testVect = vectorizePids(testData, diagTerms, includeCid=True, includeTerm=False)		
	pprint.pprint(testVect)
	testArray = featurizer.transform(testVect).toarray()	
	tn = 0
	fn = 0
	tp = 0
	fp = 0
	for i, tv in enumerate(testArray):				
		l = testData[testData.keys()[i]]
		pred = model.predict(tv)[0]
		print 'prediction: '+str(pred)
		print 'actual: '+str(l)
		if pred == l:
			if pred == 0:
				tn += 1
			else:
				tp += 1
		else:
			miss = featurizer.inverse_transform(tv)			
			print 'missed!'
			print 'probabilities: '+str(model.predict_proba(tv))										
			if pred == 0:
				fn += 1
			else:
				fp += 1
	print 'tn: '+str(tn)
	print 'tp: '+str(tp)
	print 'fn: '+str(fn)
	print 'fp: '+str(fp)
	print 'acc: '+str(float(tp+tn)/float(tp+tn+fn+fp))
	if tp + fp > 0:
		print 'ppv: '+str(float(tp)/float(tp+fp))
	fimp = featurizer.inverse_transform(model.feature_importances_)	
	writeFeatureImportance(fimp[0], featurefile)


if __name__ == "__main__":
	print >> sys.stderr, 'usage <dataFile> <number of samples> <ignoreFile> <featureOutputFile> <classifierIn> <featurizerIn> labs|meds|terms|cids|codes'
	data = getFromFile(int(sys.argv[2]), sys.argv[1], 'cache')		
	dt = None
	if '-dt' in sys.argv:
		dt = sys.argv[6:]

	predict(data, sys.argv[3], sys.argv[4], dt, sys.argv[7:], sys.argv[5], sys.argv[6])
	
	




