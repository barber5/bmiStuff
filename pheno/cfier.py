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
	

	data = {'1065445': 0, '349079': 0, '1047690': 0, '58229': 1, '49538': 1, '775808': 0, '923220': 1, '1190015': 1, '1082321': 0, '661233': 1, '447144': 1, '524321': 1, '1180951': 0, '92554': 0, '187482': 0, '570606': 1, '73494': 0, '1223694': 0, '993554': 1, '1124300': 1, '1093133': 0, '779421': 1, '1000064': 1, '632880': 1, '483586': 1, '50303': 0, '1085769': 1, '211763': 0, '1066368': 1, '494998': 0, '304597': 0, '389828': 0, '751531': 1, '880568': 0, '221220': 0, '1180276': 1, '801454': 0, '810527': 0, '239215': 1, '753613': 0, '133092': 0, '386087': 1, '1026588': 1, '1146222': 1, '327276': 0, '1024277': 0, '398234': 1, '854853': 0, '537366': 1, '692467': 1, '790186': 0, '330875': 1, '456704': 0, '1221330': 1, '41305': 0, '502443': 1, '239861': 0, '1223297': 1, '643393': 0, '498302': 0, '904768': 1, '684158': 1, '908671': 1, '120036': 0, '887404': 1, '611703': 1, '937295': 0, '566153': 1, '443751': 1, '1127621': 0, '715847': 0, '456029': 1, '275304': 0, '1057370': 1, '1147923': 1, '433877': 0, '766665': 1, '314403': 1, '216459': 0, '946917': 0, '398690': 1, '511432': 0, '394871': 1, '539470': 1, '1253276': 1, '655576': 0, '827851': 1, '8129': 1, '193462': 1, '938909': 0, '599043': 0, '964452': 0, '636496': 1, '336124': 1, '270': 0, '1168795': 0, '423696': 0, '870039': 1, '1146744': 0, '294155': 1, '665516': 1, '667498': 1, '162746': 1, '121275': 0, '194125': 1, '409101': 0, '577786': 0, '41911': 0, '659312': 1, '366477': 1, '537702': 1, '223445': 0, '1218008': 0, '1015963': 0, '895157': 1, '117403': 0, '895092': 1, '230807': 0, '914015': 0, '1116127': 1, '368052': 0, '141153': 0, '1200289': 1, '275176': 0, '421879': 1, '479854': 1, '33235': 1, '622112': 1, '297998': 1, '624067': 1, '370661': 1, '905732': 0, '264594': 1, '1013188': 1, '1131744': 1, '1020977': 0, '475222': 1, '856072': 1, '1185465': 1, '305294': 1, '418180': 1, '588770': 1, '866787': 1, '434431': 0, '1161436': 0, '1006900': 0, '892527': 1, '973351': 0, '692152': 1, '309723': 1, '244217': 0, '27868': 0, '561981': 1, '1076416': 1, '108247': 0, '1043925': 1, '242480': 1, '13819': 1, '1236070': 0, '118266': 0, '18073': 1, '379562': 1, '912644': 0, '13062': 0, '1062530': 1, '983736': 1, '187416': 0, '1102822': 0, '790581': 0, '1022362': 0, '677457': 0, '1084159': 0, '502573': 1, '147990': 1, '374180': 0, '831175': 0, '1085746': 0, '1151728': 1, '1218013': 0, '121965': 0, '970388': 1, '462721': 0, '696362': 1, '254224': 0, '87051': 1, '709179': 1, '1027263': 0, '976364': 0, '379573': 0, '599998': 1, '401304': 0, '568008': 0, '96072': 0, '307424': 0, '251443': 0, '11848': 0, '555222': 0}

	testData = {'200741': 1, '349079': 0, '465695': 0, '997754': 1, '417963': 0, '966833': 1, '755164': 1, '842473': 0, '226563': 0, '903817': 1, '1022117': 0, '124692': 0, '1245625': 0, '813714': 0, '710418': 0, '24473': 0, '949624': 0, '935463': 0, '695578': 1, '543589': 0, '1181776': 1, '111426': 1, '334036': 1, '1069058': 1, '131574': 0, '403664': 1, '1195515': 1, '1162551': 0, '867231': 1, '367497': 1, '212373': 1, '913998': 1, '1051449': 0, '440396': 1, '670026': 1, '736693': 0, '169495': 1, '1164347': 0, '314403': 1, '853327': 0, '592670': 1, '979492': 1, '658763': 1, '783407': 0, '599043': 0, '623318': 0, '92134': 1, '1074005': 0, '1152555': 0, '1049760': 1, '621046': 0, '1155442': 1, '837806': 1, '1103699': 0, '944245': 0, '929584': 0, '66284': 0, '384259': 0, '470953': 1, '810763': 1, '717564': 1, '1228012': 1, '642456': 1, '54483': 1, '904480': 1, '953716': 1, '949078': 1, '800860': 0, '825136': 0, '918502': 0, '28577': 0, '992476': 0, '126736': 0, '380070': 1, '282938': 1, '962742': 0, '541395': 1, '219905': 0, '262570': 0, '19833': 1, '968346': 1, '607340': 1, '304597': 0, '134258': 1, '922861': 0, '1447': 1, '955653': 1, '617784': 1, '287685': 1, '131624': 0, '108429': 1, '586383': 1, '420355': 0, '1185465': 1, '925823': 0, '184717': 0, '980669': 0, '568008': 0, '11848': 0}
	runCfier(data, testData, sys.argv[1])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
