import sys,os, pprint, json, random, pprint
from math import sqrt
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCui import getCuis, r, decomp, compIt
from getTermByID import getTerm, getTermCui, getIngredients, getIngredient, getLab, getConcept
from queryByCode import getPids
from sklearn.feature_extraction import DictVectorizer as FH
from sklearn.ensemble import RandomForestClassifier as rfc

meta = {
	'termCounting': 'boolean',
	'labCounting': 'categorical_status',
	'labCounting2': 'bag',
	'prescriptionCounting': 'bag',
	'codeCounting': 'bag'
}

stop_terms = range(10)
stop_terms.extend([11, 13, 20, 21, 26, 39, 32, 40, 43, 46, 54, 18, 1028, 116, 339, 31, 40, 183, 1355, 407, 59, 252, 1763, 2423, 6053, 5818, 7160, 47582, 3966, 3746, 130])

cuiCache = {}

def getPidsFromFile(fname):
	pids = {}
	with open(fname, 'r') as fi:
		while True:
			line = fi.readline()
			if line == '':
				break
			lineA = line.split('\t')
			pid = lineA[0]
			label = lineA[1]
			pids[pid] = label
	return pids

def getFeatName(metaDict, presentation=False):
	if metaDict['type'] == 'term':
		term = metaDict['term']
		if not presentation or str(term['familyHistory']) == '1':
			return 'term:'+str(term['tid'])+':'+str(term['negated'])+':'+str(term['familyHistory'])
		else:
			return 'term-presentation:'+str(term['tid'])+':'+str(term['negated'])+':'+str(term['familyHistory'])
	if metaDict['type'] == 'lab':
		lab = metaDict['lab']
		if not presentation:
			name = 'lab:'+lab['proc']+':'+str(lab['component'])
		else:
			name = 'lab-presentation:'+lab['proc']+':'+str(lab['component'])
		return name
	if metaDict['type'] == 'prescription':
		p = metaDict['prescription']
		i = metaDict['ingredient']
		if p['order_status'].find('Discontinue') != -1:
			val = 'disco'
		else:
			val = 'ongoing'
		if not presentation:
			return 'prescription:'+str(i)+':'+val
		else:
			return 'prescription-presentation:'+str(i)+':'+val
	if metaDict['type'] == 'code':
		v = metaDict['code'].strip()
		if not presentation:
			return 'code:'+str(v)
		else:
			return 'code-presentation:'+str(v)
	if metaDict['type'] == 'cid':
		cui = metaDict['term']['cui']		
		return 'cid:'+str(cui)

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def vectorizePids(data, diagTerms=None, includeCid=False, includeLab=True, includeTerm=True, includeCode=True, includePrescription=True, featureFilter={}, timeSlices=None):
	patients = []	
	print 'diagnosis terms for timeoffset: '+str(diagTerms)
	print 'stop terms: '+str(stop_terms)
	for pid, label in data.iteritems():		
		print pid				
		#print pid
		resp = r.hget('pats', pid)
		if resp == None:
			continue
		#print resp

		dd = decomp(resp)
		nextPerson = {}
		if meta['termCounting'] == 'noteboolean':  # we add 1 to a term count for each note it appears in
			noteTerms = set([])

		if diagTerms:
			print >> sys.stderr, 'patient: '+str(pid)+' label: '+str(label)
			minOffset = float('inf')			
			for n in dd['notes']:
				for t in n['terms']:
					if int(t['tid']) in stop_terms:
						continue
					if str(t['tid']) in diagTerms and int(t['negated']) == 0 and int(t['familyHistory']) == 0:					
						if float(n['timeoffset']) < minOffset:
							minOffset = float(n['timeoffset'])
					elif label == 0:
						if minOffset == float('inf'):
							minOffset = n['timeoffset']
						elif random.random() > .5:
							minOffset = n['timeoffset']
			print >> sys.stderr, 'minOffset: '+str(minOffset)			
		if includeTerm:
			for n in dd['notes']:
				if diagTerms and float(n['timeoffset']) < minOffset:
					continue
				if diagTerms and float(n['timeoffset']) == minOffset:					
					presentation = False
				else:
					presentation = False
				for t in n['terms']:
					if int(t['tid']) in stop_terms:
						continue
					feat = getFeatName({'type': 'term', 'term': t}, presentation)
					if feat in featureFilter:
						continue
					if feat not in nextPerson:
						nextPerson[feat] = 0
					if meta['termCounting'] == 'bag':
						nextPerson[feat] += 1
					elif meta['termCounting'] == 'boolean':
						nextPerson[feat] = 1
					elif meta['termCounting'] == 'noteboolean':
						lookup = (n['nid'], feat)
						if lookup in noteTerms:
							continue
						else:
							nextPerson[feat] += 1
							noteTerms.add(lookup)
					elif meta['termCounting'] == 'kernel':
						nextPerson[feat] += kernelize(meta['termKernel'], 1, n['timeoffset'], timeSlices[pid])
		if includeCid:
			for n in dd['notes']:
				if diagTerms and float(n['timeoffset']) < minOffset:
					continue
				if diagTerms and float(n['timeoffset']) == minOffset:					
					presentation = False
				else:
					presentation = False
				for t in n['terms']:					
					if int(t['tid']) in stop_terms:
						continue					
					feat = getFeatName({'type': 'term', 'term': t})
					print 'tid: '+str(t['tid'])
					if feat in featureFilter:
						continue
					feat = getFeatName({'type': 'cid', 'term': t}, presentation)
					if not feat:
						continue
					if feat in featureFilter:
						continue
					if feat not in nextPerson:
						nextPerson[feat] = 0
					if meta['termCounting'] == 'bag':
						nextPerson[feat] += 1
					elif meta['termCounting'] == 'boolean':
						nextPerson[feat] = 1
					elif meta['termCounting'] == 'noteboolean':
						lookup = (n['nid'], feat)
						if lookup in noteTerms:
							continue
						else:
							nextPerson[feat] += 1
							noteTerms.add(lookup)
					elif meta['termCounting'] == 'kernel':
						nextPerson[feat] += kernelize(meta['termKernel'], 1, n['timeoffset'], timeSlices[pid])
		if includeLab:
			if meta['labCounting'] == 'average':
				labCounts = {}
			for l in dd['labs']:
				if diagTerms and float(l['timeoffset']) < minOffset:
					continue
				if diagTerms and float(l['timeoffset']) == minOffset:
					presentation = True
				else:
					presentation = False
				if 'ord_num' not in l or not l['ord_num'] or l['ord_num'] == '':
					continue
				feat = getFeatName({'type': 'lab', 'lab': l}, presentation)
				if feat in featureFilter:
					continue
				if meta['labCounting'] == 'average':
					if feat not in labCounting:
						labCounting[feat] = {'total': 0, 'count': 0}
					labCounting[feat]['count'] += 1
					labCounting[feat]['total'] += l['ord_num']
				elif meta['labCounting'] == 'categorical_status':
					if 'result_flag' not in l or not l['result_flag'] or l['result_flag'] == '':
						val = 'normal'
					else:
						val = l['result_flag']
					feat += ':'+str(val)
					if feat not in nextPerson:
						nextPerson[feat] = 0
					if meta['labCounting2'] == 'boolean':
						nextPerson[feat] = 1
					elif meta['labCounting2'] == 'bag':
						nextPerson[feat] += 1
				elif meta['labCounting'] == 'kernel':
					if 'result_flag' not in l or not l['result_flag'] or l['result_flag'] == '':
						val = 'normal'
					else:
						val = l['result_flag']
					feat += ':'+str(val)
					if feat in featureFilter:
						continue
					if feat not in nextPerson:
						nextPerson[feat] = 0
					nextPerson[feat] += kernelize(meta['labKernel'], 1, l['timeoffset'], timeSlices[pid])  # timeSlices is a mapping from pids to timeoffsets of interest
			if meta['labCounting'] == 'average':
				for k,v in labCounting.iteritems():
					nextPerson[k] = float(v['total']) / float(v['count'])
		if includePrescription:
			for p in dd['prescriptions']:
				if diagTerms and float(p['timeoffset']) < minOffset:
					continue
				if diagTerms and float(p['timeoffset']) == minOffset:
					presentation = True
				else:
					presentation = False
				ings = getIngredients(p['ingr_set_id'])
				for i in ings:
					feat = getFeatName({'type': 'prescription', 'prescription': p, 'ingredient': i}, presentation)
					if feat in featureFilter:
						continue
					if meta['prescriptionCounting'] == 'boolean':
						nextPerson[feat] = 1
					elif meta['prescriptionCounting'] == 'bag':
						if feat not in nextPerson:
							nextPerson[feat] = 0
						nextPerson[feat] += 1
					elif meta['prescriptionCounting'] == 'kernel':
						if feat not in nextPerson:
							nextPerson[feat] = 0
						nextPerson[feat] += kernelize(meta['prescriptionKernel'], 1, p['timeoffset'], timeSlices[pid])
		if includeCode:
			for v in dd['visits']:
				if diagTerms and float(v['timeoffset']) < minOffset:
					continue
				if diagTerms and float(v['timeoffset']) == minOffset:
					presentation = True
				else:
					presentation = False
				if 'icd9' in v and len(v['icd9']) > 0:
					codes = v['icd9'].split(',')
					for c in codes:						
						if 'codeCollapse' in meta and meta['codeCollapse']:
							c = code.split('.')[0]
						feat = getFeatName({'type': 'code', 'code': c}, presentation)	
						if feat in featureFilter:						
							continue
						if meta['codeCounting'] == 'boolean':
							nextPerson[feat] = 1
						elif meta['codeCounting'] == 'bag':
							if feat not in nextPerson:
								nextPerson[feat] = 0
							nextPerson[feat] += 1
						elif meta['codeCounting'] == 'kernel':
							if feat not in nextPerson:
								nextPerson[feat] = 0
							nextPerson[feat] += kernelize(meta['codeKernel'], 1, v['timeoffset'], timeSlices[pid])	
		nextPerson['meta-visits'] = len(dd['visits'])	
		nextPerson['meta-notes'] = len(dd['notes'])
		nextPerson['meta-labs'] = len(dd['labs'])
		nextPerson['meta-prescriptions'] = len(dd['prescriptions'])

		patients.append(nextPerson)
	

	return patients



def filterDataByLabel(data, label):
	result = {}
	for pid,lab in data.iteritems():
		if lab == label:
			result[pid] = lab
	return result

def trainModel(trainData, diagTerm=None, featureFilter={},includeCid=False, includeLab=True, includeTerm=True, includeCode=True, includePrescription=True):		
	trainVect = vectorizePids(trainData, diagTerm, featureFilter=featureFilter, includeLab=includeLab, includeCode=includeCode, includeTerm=includeTerm, includePrescription=includePrescription, includeCid=includeCid)	
	counts = {}
	for patient in trainVect:
		for feat, val in patient.iteritems():
			if feat not in counts:
				counts[feat] = 0
			counts[feat] += 1
	newTrain = []
	for patient in trainVect:
		newPatient = {}
		for feat, val in patient.iteritems():
			if float(val) / float(len(trainVect)) > -1:
				newPatient[feat] = val
		
		newTrain.append(newPatient)
	fh = FH()
	trainArray = fh.fit_transform(newTrain).toarray()	
	try:
		print 'feature dimensions n_samples x n_features'
		print trainArray.shape
	except Exception as e:
		None
	n_estimators = int(round(sqrt(trainArray.shape[1])))*2
	print 'n_estimators: '+str(n_estimators)
	tree = rfc(n_estimators=n_estimators, n_jobs=(n_estimators/10))		
	tree.fit(trainArray, trainData.values())	
	return (tree, fh)
	#train the model
	# return

def resolveFeature(f):	
	if f.find('term') == 0:
		tArr = f.split(':')
		term = getTerm(tArr[1])
		tArr[1] = str(tArr[1])+'('+str(term)+')'
		return ':'.join(tArr)
	elif f.find('lab') == 0:
		tArr = f.split(':')
		lab = getLab(tArr[2])
		tArr[2] = str(tArr[2])+'('+str(lab)+')'
		return ':'.join(tArr)

	elif f.find('prescription') == 0:
		tArr = f.split(':')
		ing = getIngredient(tArr[1])
		tArr[1] = str(tArr[1])+'('+str(ing)+')'
		return ':'.join(tArr)
	elif f.find('cid') == 0:
		tArr = f.split(':')
		cid = getTermCui(tArr[1])
		if cid:
			conc = getConcept(cid)
		else:
			conc=None
		tArr[1] = str(tArr[1])+'('+str(cid)+'('+str(conc)+')'
		return ':'.join(tArr)
	else:
		return f

def writeFeatureImportance(fimp, fileName):
	with open(fileName, 'w') as fi:
		for f, imp in fimp.iteritems():
			f = resolveFeature(f)
			fi.write(str(f)+'\t%.8f\n'%float(imp))

def getIgnoreCodes(ignoreFile):
	result = set([])
	with open(ignoreFile, 'r') as fi:
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			result.add(line)
	return result

def runCfier(trainData, testData, ignoreFile, featurefile, diagTerms, featSets):	
	ignore = getIgnoreCodes(ignoreFile)
	print >> sys.stderr, 'ignoring: '+str(ignore)
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

	(model, featurizer) = trainModel(trainData, diagTerms, featureFilter=ignore, includeLab=includeLab, includeCode=includeCode, includeTerm=includeTerm, includePrescription=includePrescription, includeCid=includeCid)	
	testVect = vectorizePids(testData, diagTerms, includeCid=includeCid, includeTerm=includeTerm)		
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


	# for each in training, predict with our mod and see if we're right or not
	# calculate stats and see what the news is
def getRandoms(num):
	res = r.hget('codes', 'random')
	li = json.loads(decomp(res))
	result = {}
	while len(result) < num:
		next = str(random.choice(li))
		result[next] = 0
	return result

def getFromFile(num, fileName):
	pids = set([])
	result = {}
	with open(fileName, 'r') as fi:
		fi.readline()
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split(' ')
			#print lineArr
			pid = lineArr[2]
			pids.add(pid)
	pids = list(pids)
	while len(result) < num:
		next = str(random.choice(pids))
		resp = r.hget('pats', next)
		if not resp:
			continue
		result[next] = 1
	return result


if __name__ == "__main__":	
	if len(sys.argv) < 9:
		print 'usage: <posFile> <posNum> <negNum> <testProportion> <ignoreFile> <featureOutputFile> <diagTerm> <[featureSets] labs|meds|terms|codes|cids>'
		sys.exit(1)
	test = {}
	train = {}
	negs = getRandoms(int(sys.argv[3]))
	pos = getFromFile(int(sys.argv[2]), sys.argv[1])
	for n, label in negs.iteritems():
		if random.random() < float(sys.argv[4]):
			test[n] = label
		else:
			train[n] = label
	for p, label in pos.iteritems():
		if random.random() < float(sys.argv[4]):			
			test[p] = label
		else:
			train[p] = label	
	dt = None
	if '-dt' in sys.argv:
		dt = sys.argv[7:]
	runCfier(train, test, sys.argv[5], sys.argv[6], dt, sys.argv[7:])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
