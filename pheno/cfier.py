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

def resolveFeature(f):
	if f.find('term') == 0:
		tArr = f.split(':')
		term = getTerm(tArr[1])
		tArr[1] = term
		return ':'.join(tArr)
	elif f.find('lab') == 0:
		tArr = f.split(':')
		lab = getLab(tArr[2])
		tArr[2] = lab
		return ':'.join(tArr)

	elif f.find('prescription') == 0:
		tArr = f.split(':')
		ing = getIngredient(tArr[1])
		tArr[1] = ing
		return ':'.join(tArr)
	else:
		return f

def writeFeatureImportance(fimp, fileName):
	with open(fileName, 'w') as fi:
		for f, imp in fimp.iteritems():
			f = resolveFeature(f)
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
	

if __name__ == "__main__":
	

	data = {'1065445': 0, '20444': 0, '538877': 1, '587179': 1, '279910': 1, '483336': 1, '232198': 1, '733052': 0, '1027460': 0, '8860': 1, '560484': 1, '306470': 1, '264241': 1, '813714': 0, '1205620': 1, '892723': 0, '119234': 1, '584410': 1, '554397': 0, '707730': 0, '628593': 0, '551029': 1, '124987': 1, '685648': 0, '893959': 1, '404215': 1, '990891': 0, '764501': 0, '599547': 0, '892851': 0, '498302': 0, '1164996': 0, '263038': 1, '277007': 0, '1084892': 0, '608660': 0, '632138': 1, '524270': 0, '275304': 0, '1069821': 1, '754563': 0, '981889': 1, '186134': 0, '676570': 1, '869336': 0, '511239': 0, '971827': 1, '549128': 0, '608776': 0, '503464': 1, '1129654': 1, '1213205': 0, '554272': 0, '11617': 0, '81755': 1, '466093': 1, '106960': 0, '946921': 1, '809152': 1, '699894': 0, '866081': 1, '1011679': 1, '793427': 0, '1084872': 0, '182344': 0, '438420': 1, '146019': 1, '28922': 1, '1051178': 0, '128193': 1, '804004': 0, '372238': 1, '1202161': 1, '927548': 1, '495435': 0, '1168334': 0, '201160': 1, '1085542': 1, '324080': 0, '999083': 0, '40111': 1, '423265': 0, '409358': 0, '183946': 0, '92969': 1, '1022361': 1, '875892': 0, '635995': 0, '124138': 1, '832774': 1, '460853': 0, '186962': 1, '765972': 1, '462721': 0, '109449': 0, '160714': 1, '894171': 1, '260754': 0, '754923': 1, '104050': 1, '1058810': 0, '555222': 0, '254538': 0, '229344': 0, '879446': 1, '1233816': 0, '869342': 0, '1024563': 1, '406568': 1, '1047995': 0, '105946': 1, '683488': 0, '420423': 0, '763986': 1, '473718': 1, '317774': 1, '52953': 0, '557760': 0, '724739': 1, '865038': 1, '553520': 0, '195062': 1, '1194823': 1, '354249': 1, '978496': 0, '211763': 0, '190299': 1, '433443': 1, '888192': 0, '910341': 1, '123315': 1, '853326': 0, '798805': 0, '793221': 0, '292171': 1, '563257': 1, '325560': 1, '1111035': 1, '58761': 0, '1152555': 0, '242190': 0, '1250799': 1, '423696': 0, '612334': 0, '811631': 1, '682776': 1, '826467': 0, '389828': 0, '4343': 0, '26747': 0, '702651': 1, '1009125': 0, '840499': 1, '131858': 1, '273571': 1, '20940': 0, '145704': 1, '1208331': 1, '270': 0, '894854': 1, '691779': 1, '709863': 0, '843282': 0, '35800': 0, '1065077': 0, '59745': 1, '1194649': 1, '1169431': 0, '72522': 1, '286185': 1, '223833': 0, '450174': 0, '1109060': 0, '187416': 0, '1176047': 0, '1206183': 0, '775371': 1, '120451': 0, '385768': 0, '561303': 0, '900978': 1, '116572': 1, '523732': 1, '306105': 1, '356220': 1, '902926': 1, '491691': 0, '1241253': 1, '926586': 0, '319002': 1, '1082321': 0, '542060': 0, '954686': 0, '92554': 0, '224952': 0, '75490': 0, '494998': 0, '577328': 1, '107518': 0, '1219560': 1, '734153': 1, '476874': 0, '636172': 1, '692898': 0, '102501': 1, '964452': 0, '236168': 1, '946194': 0, '920261': 1, '322738': 1, '916343': 1, '433877': 0, '128174': 1, '563089': 1, '1033444': 0, '243624': 0, '369443': 0, '825722': 1, '1145279': 0, '29736': 1, '929056': 0, '432683': 1, '621046': 0, '302403': 1, '493526': 1, '908875': 1, '328246': 1, '626621': 1, '259062': 1, '202167': 1, '1230477': 0, '184567': 1, '1212428': 0, '1123205': 1, '550184': 1, '529550': 0, '252128': 0, '351398': 1, '173219': 0, '692418': 1, '35885': 0, '900845': 0, '2894': 0, '918502': 0, '154423': 1, '630898': 1, '938017': 0, '549367': 0, '1218008': 0, '557949': 0, '535862': 0, '242481': 1, '135863': 0, '821398': 0, '907244': 0, '589492': 0, '708096': 0, '480165': 0, '881638': 1, '1122175': 0, '1056093': 0, '55607': 0, '229923': 1, '190770': 1, '1255823': 1, '813245': 1, '1122671': 1, '976364': 0, '899200': 1, '1201458': 1, '571173': 1, '1061808': 0, '875436': 0, '1159527': 0, '572787': 1, '1107965': 1, '491512': 1, '18316': 1, '715955': 1, '38199': 1, '12776': 1, '1147302': 0, '793067': 1, '1099173': 0, '1093133': 0, '794158': 1, '470105': 1, '512487': 1, '554212': 0, '581522': 0, '756191': 0, '481968': 1, '810527': 0, '1022117': 0, '1247887': 0, '792824': 1, '746224': 1, '496495': 1, '502157': 1, '134926': 1, '634292': 1, '303061': 1, '78559': 0, '391799': 1, '70177': 1, '108205': 1, '1219941': 0, '612120': 0, '1215446': 0, '1072076': 0, '231738': 0, '611505': 1, '958054': 1, '587294': 0, '577026': 0, '929206': 1, '937980': 0, '656371': 0, '1019477': 1, '1103699': 0, '1249288': 1, '406712': 1, '1028035': 1, '996144': 1, '877466': 1, '114569': 1, '312990': 1, '219768': 1, '1046193': 0, '921215': 1, '84819': 0, '637239': 1, '358887': 0, '29253': 1, '914015': 0, '314786': 0, '1166184': 1, '502775': 1, '381369': 0, '466743': 1, '405284': 1, '545529': 1, '371030': 1, '532105': 1, '28577': 0, '1017538': 0, '788782': 0, '817904': 0, '591013': 1, '987525': 1, '773686': 1, '1126146': 1, '738184': 0, '180985': 0, '1033494': 1, '482748': 1, '795762': 0, '858729': 0, '784992': 0, '1021262': 1, '370109': 0, '932707': 1, '563480': 0, '631374': 1, '544519': 0, '774458': 1, '1014413': 0, '297619': 0, '1061101': 0, '1193062': 1}

	testData = {'200741': 1, '349079': 0}
	runCfier(data, testData, sys.argv[1])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
