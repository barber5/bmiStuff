import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCui import getCuis, r, decomp, compIt
from getTermByID import getTerm, getTermCui, getIngredients, getIngredient, getLab
from queryByCode import getPids
from sklearn.feature_extraction import DictVectorizer as FH
from sklearn.ensemble import RandomForestClassifier as rfc

meta = {
	'termCounting': 'noteboolean',
	'labCounting': 'categorical_status',
	'labCounting2': 'bag',
	'prescriptionCounting': 'bag',
	'codeCounting': 'bag'
}

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

def getFeatName(metaDict):
	if metaDict['type'] == 'term':
		term = metaDict['term']
	
		return 'term:'+str(term['tid'])+':'+str(term['negated'])+':'+str(term['familyHistory'])
	if metaDict['type'] == 'lab':
		lab = metaDict['lab']
		name = 'lab:'+lab['proc']+':'+str(lab['component'])									
		return name
	if metaDict['type'] == 'prescription':
		p = metaDict['prescription']
		i = metaDict['ingredient']
		if p['order_status'].find('Discontinue') != -1:
			val = 'disco'
		else:
			val = 'ongoing'
		return 'prescription:'+str(i)+':'+val
	if metaDict['type'] == 'code':
		v = metaDict['code'].strip()
		return 'code:'+str(v)

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def vectorizePids(data, includeCid=False, includeLab=True, includeTerm=True, includeCode=True, includePrescription=True, featureFilter={}, timeSlices=None):
	patients = []
	print featureFilter
	for pid, label in data.iteritems():
		print pid
		resp = r.hget('pats', pid)
		#print resp

		dd = decomp(resp)
		nextPerson = {}
		if meta['termCounting'] == 'noteboolean':  # we add 1 to a term count for each note it appears in
			noteTerms = set([])

		if includeTerm:
			for n in dd['notes']:
				for t in n['terms']:
					feat = getFeatName({'type': 'term', 'term': t})
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
				if 'ord_num' not in l or not l['ord_num'] or l['ord_num'] == '':
					continue
				feat = getFeatName({'type': 'lab', 'lab': l})
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
				ings = getIngredients(p['ingr_set_id'])
				for i in ings:
					feat = getFeatName({'type': 'prescription', 'prescription': p, 'ingredient': i})
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
				if 'icd9' in v and len(v['icd9']) > 0:
					codes = v['icd9'].split(',')
					for c in codes:						
						if 'codeCollapse' in meta and meta['codeCollapse']:
							c = code.split('.')[0]
						feat = getFeatName({'type': 'code', 'code': c})	
						if feat in featureFilter:
							print 'ignoring: '+str(feat)
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

		patients.append(nextPerson)
	

	return patients



def filterDataByLabel(data, label):
	result = {}
	for pid,lab in data.iteritems():
		if lab == label:
			result[pid] = lab
	return result

def trainModel(trainData, ignore={}):		
	trainVect = vectorizePids(trainData,featureFilter=ignore)	
	fh = FH()
	trainArray = fh.fit_transform(trainVect).toarray()	
	tree = rfc(verbose=100, n_estimators=128, n_jobs=10)	
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

def runCfier(trainData, testData, ignoreFile, featurefile):	
	ignore = getIgnoreCodes(ignoreFile)
	print 'ignoring: '+str(ignore)
	(model, featurizer) = trainModel(trainData, ignore)	
	testVect = vectorizePids(testData)		
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
			if pred == 0:
				fn += 1
			else:
				fp += 1
	print 'tn: '+str(tn)
	print 'tp: '+str(tp)
	print 'fn: '+str(fn)
	print 'fp: '+str(fp)
	fimp = featurizer.inverse_transform(model.feature_importances_)	
	writeFeatureImportance(fimp[0], featurefile)


	# for each in training, predict with our mod and see if we're right or not
	# calculate stats and see what the news is
	

if __name__ == "__main__":
	data = {'1217659': 1, '363104': 1, '594217': 0, '77043': 0, '1047690': 0, '929584': 0, '538877': 1, '134120': 0, '756191': 0, '1072262': 0, '684533': 0, '998975': 1, '413600': 1, '336606': 1, '226563': 0, '98822': 1, '193291': 1, '118136': 1, '337038': 1, '160815': 0, '794158': 1, '124346': 0, '327065': 1, '192895': 1, '1023461': 0, '1063891': 0, '607960': 0, '880568': 0, '681637': 1, '70377': 0, '753613': 0, '1160243': 0, '636172': 1, '564452': 1, '215026': 0, '422452': 1, '219905': 0, '692898': 0, '21440': 0, '724739': 1, '53527': 0, '1038798': 1, '583135': 0, '1196446': 0, '44040': 1, '865038': 1, '548796': 1, '619911': 0, '865522': 0, '543102': 0, '1151490': 0, '1108425': 1, '134926': 1, '911638': 1, '1248158': 1, '950722': 0, '634292': 1, '1110605': 1, '524270': 0, '784213': 1, '370467': 1, '758632': 0, '429476': 1, '443996': 1, '175354': 1, '21462': 1, '629321': 0, '612120': 0, '17313': 1, '319427': 0, '327748': 0, '139643': 0, '271891': 0, '193674': 1, '309978': 0, '818832': 1, '1015225': 1, '561224': 0, '511239': 0, '1158143': 0, '825722': 1, '456329': 1, '27981': 1, '1006900': 0, '827991': 1, '660937': 0, '1198969': 0, '270903': 0, '1178234': 0, '466093': 1, '225623': 1, '754387': 0, '1146744': 0, '1249288': 1, '958183': 1, '222466': 0, '313247': 1, '645391': 1, '1145279': 0, '798156': 1, '1169997': 0, '27990': 1, '409101': 0, '687824': 1, '259062': 1, '420541': 1, '712061': 1, '475717': 1, '231738': 0, '702651': 1, '466453': 1, '338875': 0, '543481': 0, '1212428': 0, '1123205': 1, '772295': 1, '403886': 0, '1175017': 0, '361950': 1, '777419': 0, '408972': 1, '938003': 1, '832187': 1, '252128': 0, '245517': 1, '78579': 1, '422316': 0, '111937': 0, '275176': 0, '498768': 0, '572355': 0, '221220': 0, '333172': 1, '463412': 0, '76709': 0, '1046739': 0, '635618': 0, '32274': 0, '992905': 0, '209529': 1, '916257': 0, '1070530': 1, '938017': 0, '1218008': 0, '342177': 1, '33452': 0, '614413': 0, '1256570': 0, '790668': 0, '632474': 0, '922861': 0, '617674': 1, '319264': 1, '1022361': 1, '858448': 1, '646682': 0, '11848': 0, '795762': 0, '413294': 1, '1206183': 0, '263005': 1, '620428': 1, '480165': 0, '790186': 0, '836918': 1, '270658': 1, '631374': 1, '441819': 1, '765972': 1, '900978': 1, '190770': 1, '127860': 0, '971700': 0, '768484': 1, '999895': 1, '1061101': 0, '1128469': 1, '737718': 1, '925823': 0, '248326': 1, '571173': 1, '568008': 0, '1092346': 1, '89871': 1, '333815': 1, '1218795': 0, '855285': 0, '1193062': 1, '39054': 0, '353750': 1}

	testData = {'1124803': 1, '731110': 0, '1176047': 0, '77296': 1, '1125430': 1, '425224': 0, '451665': 0, '891315': 0, '1172204': 1, '866081': 1}
	runCfier(data, testData, sys.argv[1], sys.argv[2])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
