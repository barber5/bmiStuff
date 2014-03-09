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

def runCfier(trainData, testData):	
	(model, featurizer) = trainModel(trainData)	
	testVect = vectorizePids(testData)	
	pprint.pprint(testVect)
	testArray = featurizer.transform(testVect).toarray()
	print testArray
	for i, tv in enumerate(testArray):				
		l = trainData[trainData.keys()[i]]
		print 'prediction: '+str(model.predict(tv))
		print 'actual: '+str(l)

	# for each in training, predict with our mod and see if we're right or not
	# calculate stats and see what the news is

	None

if __name__ == "__main__":
	data = {'934488': 0, '842473': 0, '186134': 0, '226563': 0, '885330': 1, '1231865': 1, '75490': 0, '1145279': 0, '644770': 1, '577806': 0, '764828': 0, '318420': 1, '577341': 1, '1117400': 1, '118996': 1, '1240011': 0, '131046': 1, '636879': 1, '1026588': 1, '962269': 0, '756019': 0, '320396': 0, '1247887': 0, '139094': 1, '962176': 1, '865522': 0, '1230817': 1, '704067': 1, '184171': 0, '1086797': 1, '1125947': 1, '1071169': 0, '1053373': 1, '376558': 1, '480801': 1, '1077188': 0, '1113362': 1, '774128': 1, '853326': 0, '423354': 1, '898967': 0, '992776': 0, '627557': 1, '1033074': 0, '196513': 0, '1161358': 0, '943371': 0, '299702': 1, '555366': 0, '222466': 0, '517988': 0, '385270': 0, '135843': 0, '1170950': 1, '185028': 1, '865086': 0, '149870': 1, '1141112': 1, '520986': 1, '929023': 0, '1214335': 0, '1200289': 1, '998469': 1, '1070674': 0, '541489': 1, '905732': 0, '59352': 1, '238423': 0, '5659': 0, '915182': 1, '1042914': 1, '912889': 1, '789316': 1, '48030': 0, '973351': 0, '390508': 1, '423265': 0, '439303': 1, '987543': 0, '478005': 1, '1008311': 1, '44890': 1, '787771': 1, '1166744': 1, '782920': 0, '709668': 0, '284241': 0, '568396': 1, '1082771': 0, '458690': 1, '904731': 0, '764840': 0, '1192363': 0, '371094': 1, '1157295': 0, '1185465': 1, '449198': 1, '742020': 0, '919184': 0}
	testData = {'483604': 0, '214241': 1, '385270': 0, '924780': 0, '1059971': 1, '416120': 0, '2218': 0, '477134': 1, '662913': 1, '249997': 1, '693795': 1, '332568': 1, '777419': 0, '116619': 1, '99949': 0, '1164890': 0, '989221': 1, '156187': 1, '26747': 0, '992905': 0}
	runCfier(data, testData)
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
