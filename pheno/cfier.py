import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCui import getCuis, r, decomp, compIt
from getTermByID import getTerm, getTermCui, getIngredients
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
		v = metaDict['code']
		return 'code:'+str(v)

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def vectorizePids(data, includeCid=False, includeLab=True, includeTerm=True, includeCode=True, includePrescription=True, featureFilter={}, timeSlices=None):
	patients = []
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

def trainModel(trainData):		
	trainVect = vectorizePids(trainData)	
	fh = FH()
	trainArray = fh.fit_transform(trainVect).toarray()	
	tree = rfc(verbose=100)	
	tree.fit(trainArray, trainData.values())	
	return (tree, fh)
	#train the model
	# return

def writeFeatureImportance(fimp, fileName):
	with open(fileName, 'w') as fi:
		for f, imp in fimp.iteritems():
			fi.write(str(f)+'\t'+str(imp)+'\n')


def runCfier(trainData, testData, featurefile):	
	(model, featurizer) = trainModel(trainData)	
	testVect = vectorizePids(testData)	
	pprint.pprint(testVect)
	testArray = featurizer.transform(testVect).toarray()
	print testArray
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

	None

if __name__ == "__main__":
	

	data = {'105673': 0, '964452': 0, '1147302': 0, '309978': 0, '771947': 0, '1223694': 0, '681216': 0, ',': 1, '1230477': 0, '57433': 0, '4': 1, '8': 1, '859881': 0, '3': 1, '284758': 0, '1065694': 0, '810527': 0, '480165': 0, '320497': 0, '215026': 0, '316813': 0, '764501': 0, '260123': 0, '716241': 0, '461488': 0, '225253': 0, '947772': 0, '216502': 0, '892851': 0, '1164996': 0, '937973': 0, '524270': 0, '673971': 0, '629321': 0, '124346': 0, '7': 1, '709668': 0, ' ': 1, '243624': 0, '1087159': 0, '1137176': 0, '196513': 0, '989105': 0, '920453': 0, '253808': 0, '1009125': 0, '538087': 0, '1124026': 0, '11617': 0, '790336': 0, '443077': 0, '619634': 0, '121275': 0, '683205': 0, '289142': 0, '1094278': 0, '656101': 0, '830973': 0, '231738': 0, '0': 1, '338875': 0, '262869': 0, '425224': 0, '1212428': 0, '2': 1, '1175017': 0, '6': 1, '359870': 0, '1255418': 0, '804004': 0, '423068': 0, '1127975': 0, '54362': 0, '606980': 0, '299803': 0, '825136': 0, '731110': 0, '100338': 0, '396602': 0, '126736': 0, '817904': 0, '144819': 0, '75646': 0, '973351': 0, '132884': 0, '993781': 0, '383680': 0, '1146762': 0, '355330': 0, '368761': 0, '971472': 0, '337659': 0, '1256141': 0, '1': 1, '308428': 0, '764828': 0, '5': 1, '1084159': 0, '1082771': 0, '9': 1, '374180': 0, '6007': 0, '296551': 0, '483604': 0, '605338': 0, '87767': 0, '908535': 0, '1061101': 0}

	testData = {'200741': 1, '349079': 0, '465695': 0, '997754': 1, '417963': 0, '966833': 1, '755164': 1, '842473': 0, '226563': 0, '903817': 1, '1022117': 0, '124692': 0, '1245625': 0, '813714': 0, '710418': 0, '24473': 0, '949624': 0, '935463': 0, '695578': 1, '543589': 0, '1181776': 1, '111426': 1, '334036': 1, '1069058': 1, '131574': 0, '403664': 1, '1195515': 1, '1162551': 0, '867231': 1, '367497': 1, '212373': 1, '913998': 1, '1051449': 0, '440396': 1, '670026': 1, '736693': 0, '169495': 1, '1164347': 0, '314403': 1, '853327': 0, '592670': 1, '979492': 1, '658763': 1, '783407': 0, '599043': 0, '623318': 0, '92134': 1, '1074005': 0, '1152555': 0, '1049760': 1, '621046': 0, '1155442': 1, '837806': 1, '1103699': 0, '944245': 0, '929584': 0, '66284': 0, '384259': 0, '470953': 1, '810763': 1, '717564': 1, '1228012': 1, '642456': 1, '54483': 1, '904480': 1, '953716': 1, '949078': 1, '800860': 0, '825136': 0, '918502': 0, '28577': 0, '992476': 0, '126736': 0, '380070': 1, '282938': 1, '962742': 0, '541395': 1, '219905': 0, '262570': 0, '19833': 1, '968346': 1, '607340': 1, '304597': 0, '134258': 1, '922861': 0, '1447': 1, '955653': 1, '617784': 1, '287685': 1, '131624': 0, '108429': 1, '586383': 1, '420355': 0, '1185465': 1, '925823': 0, '184717': 0, '980669': 0, '568008': 0, '11848': 0}
	runCfier(data, testData, sys.argv[1])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
