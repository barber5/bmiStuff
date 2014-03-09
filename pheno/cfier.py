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
def vectorizePids(data, includeCid=False, includeLab=True, includeTerm=False, includeCode=True, includePrescription=True, featureFilter={}, timeSlices=None):
	patients = []
	print featureFilter
	for pid, label in data.iteritems():
		#print pid
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
	tree = rfc(verbose=100, n_estimators=10, n_jobs=10)	
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
	data = {'302563': 0, '1065445': 0, '370644': 1, '123863': 0, '997754': 1, '109516': 0, '712762': 1, '1072262': 0, '1049642': 1, '33837': 1, '1056239': 1, '351551': 0, '11982': 0, '606170': 1, '605732': 0, '455742': 1, '1081259': 0, '1240871': 0, '1007602': 0, '318606': 1, '54855': 1, '1145279': 0, '57433': 0, '537094': 1, '444848': 1, '1049013': 0, '294922': 1, '188421': 1, '1250976': 1, '53879': 0, '620679': 1, '1194058': 1, '603904': 1, '753613': 0, '828384': 1, '881171': 1, '846041': 0, '1032053': 1, '268068': 1, '968334': 1, '875436': 0, '1214649': 1, '39705': 1, '622332': 0, '808065': 1, '853874': 0, '727744': 1, '1255720': 0, '209352': 0, '463869': 0, '863014': 1, '904768': 1, '885911': 0, '731110': 0, '608660': 0, '731005': 1, '555908': 0, '673971': 0, '331113': 1, '947772': 0, '169495': 1, '1195853': 1, '223036': 0, '833615': 0, '124346': 0, '831229': 0, '1096659': 1, '1129313': 1, '1056655': 0, '1188767': 0, '511432': 0, '753434': 1, '770314': 1, '134173': 1, '766665': 1, '557853': 0, '1009430': 1, '780846': 1, '416120': 0, '805168': 0, '326668': 0, '549128': 0, '80856': 1, '376317': 1, '563607': 1, '609490': 1, '1095214': 1, '1198969': 0, '35297': 0, '640227': 1, '201652': 1, '456400': 0, '1177207': 0, '201552': 0, '748885': 0, '655556': 1, '1077582': 1, '697488': 1, '392346': 1, '408123': 0, '730595': 1, '905788': 1, '1089122': 1, '498302': 0, '290464': 1, '541879': 1, '385270': 0, '1124505': 0, '1124740': 0, '906613': 0, '1218008': 0, '26747': 0, '520716': 1, '102531': 0, '187482': 0, '1084302': 0, '215321': 1, '974173': 0, '403886': 0, '1199656': 1, '804004': 0, '20940': 0, '832160': 1, '136562': 1, '165959': 1, '298333': 1, '1178746': 1, '258477': 1, '521938': 0, '448119': 1, '706609': 1, '900845': 0, '331922': 1, '599547': 0, '254666': 0, '87931': 1, '108793': 0, '554212': 0, '235580': 1, '387340': 0, '1164150': 1, '466925': 1, '32274': 0, '1235703': 1, '387508': 1, '1161105': 1, '1021332': 1, '423265': 0, '790668': 0, '957171': 1, '262570': 0, '720142': 1, '606980': 0, '670821': 0, '682499': 0, '1069419': 1, '369189': 0, '339934': 0, '924780': 0, '473954': 1, '968189': 1, '972290': 1, '635995': 0, '412428': 0, '1127556': 1, '497379': 0, '368761': 0, '1078438': 1, '1009145': 1, '947409': 1, '966217': 0, '1115670': 1, '1002697': 0, '1045703': 1, '607734': 1, '944245': 0, '93870': 0, '1052894': 1, '1209460': 1, '433877': 0, '654595': 0, '900188': 1, '206249': 0, '502804': 1, '983579': 1, '1004859': 0, '1236043': 0, '184717': 0, '1086209': 0, '980669': 0, '1047396': 1, '272795': 0, '984974': 1, '243562': 0, '1097053': 1, '306392': 1, '855285': 0}



	testData = {'1114789': 0, '627892': 0, '589132': 1, '256455': 1, '727952': 1, '713805': 1, '281192': 1, '819201': 1, '1047995': 0, '21': 1, '558080': 1, '274945': 1, '797806': 1, '653146': 0, '620679': 1, '57433': 0, '34729': 0, '475065': 0, '831646': 1, '1080205': 1, '442833': 1, '323115': 1, '698116': 1, '1179135': 0, '548531': 0, '555908': 0, '68013': 0, '1007717': 0, '446062': 0, '1164347': 0, '1240871': 0, '484938': 0, '1197436': 1, '447095': 0, '630028': 1, '85627': 0, '341977': 0, '1210339': 0, '607798': 1, '1006900': 0, '914556': 0, '1254012': 1, '943371': 0, '46792': 1, '301712': 0, '456400': 0, '33306': 1, '423696': 0, '612334': 0, '754387': 0, '517988': 0, '1146598': 1, '34611': 1, '39918': 0, '900582': 0, '149870': 1, '974076': 0, '214420': 1, '998469': 1, '1243232': 1, '632474': 0, '123408': 0, '467925': 1, '297619': 0, '1230114': 1, '961393': 0, '220694': 0, '365762': 1, '782152': 0, '911706': 1, '121275': 0, '423265': 0, '1044553': 1, '745233': 0, '76247': 1, '783002': 1, '39326': 1, '108247': 0, '1043679': 1, '1164890': 0, '357638': 1, '968189': 1, '404404': 0, '549764': 1, '1151728': 1, '568962': 1, '711930': 1, '88071': 0, '1057259': 1, '568779': 1, '21413': 1, '782920': 0, '990620': 1, '1154801': 1, '506941': 1, '1127424': 0, '145739': 1}

	runCfier(data, testData, sys.argv[1], sys.argv[2])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
