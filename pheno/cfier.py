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
	tn = 0
	fn = 0
	tp = 0
	fp = 0
	for i, tv in enumerate(testArray):				
		l = trainData[trainData.keys()[i]]
		pred = model.predict(tv)[0]
		print 'prediction: '+str(pred)
		print 'actual: '+str(l)
		if pred == pred:
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

	# for each in training, predict with our mod and see if we're right or not
	# calculate stats and see what the news is

	None

if __name__ == "__main__":
	data = {'425052': 1, '77043': 0, '367228': 1, '1130146': 1, '1254744': 1, '186134': 0, '733052': 0, '665674': 0, '1213205': 0, '564311': 0, '469277': 1, '294922': 1, '13249': 0, '870149': 1, '899864': 1, '892723': 0, '715928': 0, '1118446': 1, '593508': 1, '636879': 1, '239215': 1, '133092': 0, '870710': 1, '931808': 1, '764501': 0, '661233': 1, '149486': 1, '155903': 0, '173159': 0, '166253': 0, '181761': 0, '1093023': 0, '1164996': 0, '950722': 0, '608660': 0, '999147': 0, '555908': 0, '754563': 0, '411500': 1, '223036': 0, '1015730': 1, '136732': 0, '1233972': 0, '169080': 1, '618762': 1, '46262': 1, '1140029': 0, '47314': 1, '1009430': 1, '1196884': 1, '609715': 0, '511239': 0, '1202408': 1, '1034469': 0, '802543': 1, '876156': 0, '930957': 1, '878681': 0, '118331': 1, '11617': 0, '541459': 1, '748007': 1, '1080222': 1, '774528': 1, '238436': 1, '577786': 0, '699894': 0, '913696': 1, '992776': 0, '865555': 1, '895092': 1, '1145737': 0, '1214335': 0, '805144': 0, '659013': 1, '243562': 0, '422316': 0, '287118': 0, '1131744': 1, '1099093': 1, '977514': 1, '1168334': 0, '369664': 1, '1087681': 0, '386346': 0, '1139240': 1, '1082383': 1, '987543': 0, '352610': 0, '1021815': 0, '975061': 1, '635995': 0, '183946': 0, '912644': 0, '147274': 0, '945067': 0, '718402': 1, '333754': 0, '611703': 1, '578448': 0, '53174': 1, '462721': 0, '826467': 0, '537303': 1, '925823': 0, '522555': 0, '67745': 0, '49007': 0, '628815': 1, '1058552': 1, '677145': 1, '138161': 1, '786755': 1, '160815': 0, '1212839': 1, '8498': 1, '825960': 1, '1131254': 1, '977794': 0, '1069058': 1, '129780': 0, '1238295': 1, '449894': 1, '51273': 1, '1119575': 1, '643393': 0, '892446': 0, '410355': 1, '1160437': 1, '749147': 1, '900582': 0, '652093': 1, '571323': 0, '833615': 0, '888192': 0, '812976': 0, '902951': 1, '306743': 1, '798805': 0, '186290': 1, '780105': 1, '755810': 0, '608776': 0, '517650': 1, '1047358': 1, '625026': 1, '407138': 1, '442719': 1, '1198969': 0, '1177207': 0, '423696': 0, '577255': 1, '873479': 1, '41911': 0, '811736': 0, '893163': 1, '1230047': 0, '865086': 0, '26747': 0, '1239178': 1, '239880': 1, '1223655': 1, '174559': 0, '403881': 1, '57064': 1, '50285': 0, '996330': 1, '896807': 1, '238423': 0, '187482': 0, '336939': 0, '311814': 1, '1019553': 0, '118924': 1, '91256': 0, '605338': 0, '1006900': 0, '1134792': 1, '987947': 1, '1149335': 1, '1169431': 0, '147360': 1, '580806': 1, '561981': 1, '334418': 1, '317396': 0, '337092': 1, '13062': 0, '715847': 0, '450174': 0, '1176047': 0, '608458': 1, '147990': 1, '374180': 0, '1192363': 0, '307334': 0, '863696': 1, '275533': 1, '926586': 0, '563719': 1, '1082321': 0, '1200614': 1, '954686': 0, '845548': 1, '75490': 0, '456778': 1, '647696': 1, '99949': 0, '1063891': 0, '404303': 1, '24191': 1, '988030': 0, '107518': 0, '280845': 1, '378828': 1, '962269': 0, '247567': 1, '960469': 1, '1129313': 1, '532262': 1, '1092523': 0, '1109938': 1, '961489': 0, '946194': 0, '1028301': 1, '1044553': 1, '1053373': 1, '96853': 0, '595457': 1, '24473': 0, '747740': 1, '320396': 0, '625902': 0, '877710': 0, '243624': 0, '1014875': 0, '757814': 0, '1137176': 0, '373309': 1, '783407': 0, '929883': 1, '588291': 0, '538087': 0, '78174': 0, '1213707': 1, '687680': 1, '1134077': 1, '689554': 0, '147170': 0, '408123': 0, '3614': 1, '791538': 1, '914098': 0, '531765': 1, '993781': 0, '401359': 1, '529550': 0, '2587': 0, '366516': 1, '1229078': 1, '1002116': 1, '1189563': 1, '261370': 1, '851287': 1, '900845': 0, '290717': 1, '170009': 1, '863732': 0, '388308': 1, '788158': 0, '283073': 1, '865874': 1, '745233': 0, '1074448': 1, '790668': 0, '136360': 1, '135863': 0, '454170': 1, '1049021': 0, '431988': 1, '926480': 1, '1213537': 1, '468712': 1, '298796': 0, '568396': 1, '1184972': 1, '1168828': 1, '319315': 0, '891457': 1, '1169257': 0, '425965': 1, '347829': 0, '757799': 0, '387883': 1, '266152': 0, '1152116': 1, '1097358': 0, '479733': 0, '528051': 0, '788187': 1, '1244958': 1, '193513': 1, '874434': 0, '507556': 0, '367910': 1, '389308': 1, '226676': 1, '1230477': 0, '637919': 1, '498105': 0, '547686': 0, '439303': 1, '927103': 1, '1137489': 0, '736777': 0, '447397': 1, '39373': 0, '481322': 0, '502722': 1, '153043': 1, '831229': 0, '216502': 0, '1223297': 1, '152709': 1, '937973': 0, '684158': 1, '190050': 1, '117507': 1, '316382': 1, '316106': 1, '1223271': 0, '319427': 0, '830973': 0, '1215446': 0, '946917': 0, '446811': 1, '21454': 1, '920453': 0, '577026': 0, '381461': 0, '1147437': 0, '1253366': 0, '768728': 0, '1103699': 0, '929584': 0, '515280': 1, '903881': 1, '756732': 1, '910791': 1, '314786': 0, '974173': 0, '1004859': 0, '476676': 1, '440680': 1, '2218': 0, '984723': 1, '175877': 0, '1233435': 1, '640241': 0, '63078': 1, '86869': 0, '309409': 1, '358221': 0, '1164890': 0, '738184': 0, '853400': 1, '50303': 0, '1127556': 1, '318952': 0, '679754': 1, '633373': 1, '870060': 1, '736625': 0, '489909': 1, '209177': 1, '557587': 1, '686885': 1, '975393': 0, '700098': 1, '984974': 1, '669427': 1, '404092': 0}
	testData = {'483604': 0, '214241': 1, '385270': 0, '924780': 0, '1059971': 1, '416120': 0, '2218': 0, '477134': 1, '662913': 1, '249997': 1, '693795': 1, '332568': 1, '777419': 0, '116619': 1, '99949': 0, '1164890': 0, '989221': 1, '156187': 1, '26747': 0, '992905': 0}
	runCfier(data, testData)
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
