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
	

	data = {'293750': 0, '627892': 0, '813983': 0, '589492': 0, '350547': 0, ' ': 1, '677457': 0, '967088': 0, '75490': 0, ',': 1, '0': 1, '1089792': 0, '4': 1, '498105': 0, '8': 1, '898064': 0, '756191': 0, '801454': 0, '736777': 0, '280687': 0, '155903': 0, '805826': 0, '140549': 0, '155314': 0, '643393': 0, '184171': 0, '548531': 0, '999147': 0, '466634': 0, '385768': 0, '1085746': 0, '392446': 0, '935809': 0, '3': 1, '7': 1, '447095': 0, '1232108': 0, '1140029': 0, '898967': 0, '231738': 0, '1158143': 0, '783407': 0, '920453': 0, '474478': 0, '1198969': 0, '886174': 0, '1152555': 0, '301712': 0, '277239': 0, '456400': 0, '607882': 0, '621046': 0, '128187': 0, '1146744': 0, '408123': 0, '240793': 0, '197518': 0, '15554': 0, '996026': 0, '1124505': 0, '963288': 0, '900582': 0, '492846': 0, '370601': 0, '1039570': 0, '2': 1, '217132': 0, '6': 1, '387340': 0, '1070674': 0, '777419': 0, '1146068': 0, '254666': 0, '1038489': 0, '364708': 0, '238423': 0, '382317': 0, '599547': 0, '881106': 0, '549367': 0, '557949': 0, '504658': 0, '1256570': 0, '1021815': 0, '682155': 0, '740326': 0, '899279': 0, '1054980': 0, '1256141': 0, '1': 1, '5': 1, '966217': 0, '9': 1, '945067': 0, '333754': 0, '78559': 0, '319315': 0, '88071': 0, '666426': 0, '451665': 0, '296551': 0, '741647': 0, '782920': 0, '1014413': 0, '1159527': 0, '1061101': 0, '229653': 0}

	testData = {'200741': 1, '349079': 0, '465695': 0, '997754': 1, '417963': 0, '966833': 1, '755164': 1, '842473': 0, '226563': 0, '903817': 1, '1022117': 0, '124692': 0, '1245625': 0, '813714': 0, '710418': 0, '24473': 0, '949624': 0, '935463': 0, '695578': 1, '543589': 0, '1181776': 1, '111426': 1, '334036': 1, '1069058': 1, '131574': 0, '403664': 1, '1195515': 1, '1162551': 0, '867231': 1, '367497': 1, '212373': 1, '913998': 1, '1051449': 0, '440396': 1, '670026': 1, '736693': 0, '169495': 1, '1164347': 0, '314403': 1, '853327': 0, '592670': 1, '979492': 1, '658763': 1, '783407': 0, '599043': 0, '623318': 0, '92134': 1, '1074005': 0, '1152555': 0, '1049760': 1, '621046': 0, '1155442': 1, '837806': 1, '1103699': 0, '944245': 0, '929584': 0, '66284': 0, '384259': 0, '470953': 1, '810763': 1, '717564': 1, '1228012': 1, '642456': 1, '54483': 1, '904480': 1, '953716': 1, '949078': 1, '800860': 0, '825136': 0, '918502': 0, '28577': 0, '992476': 0, '126736': 0, '380070': 1, '282938': 1, '962742': 0, '541395': 1, '219905': 0, '262570': 0, '19833': 1, '968346': 1, '607340': 1, '304597': 0, '134258': 1, '922861': 0, '1447': 1, '955653': 1, '617784': 1, '287685': 1, '131624': 0, '108429': 1, '586383': 1, '420355': 0, '1185465': 1, '925823': 0, '184717': 0, '980669': 0, '568008': 0, '11848': 0}
	runCfier(data, testData, sys.argv[1])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
