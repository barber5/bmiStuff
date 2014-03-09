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
	tree = rfc(verbose=100, n_estimators=50, n_jobs=10)	
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
	data = {'1221000': 0, '571323': 0, '777505': 1, '976958': 0, '465695': 0, '587179': 1, '279910': 1, '467547': 1, '1076638': 1, '711306': 0, '121698': 1, '483336': 1, '413600': 1, '336606': 1, '232198': 1, '73494': 0, '457234': 1, '665674': 0, '193291': 1, '1213205': 0, '682155': 0, '412637': 1, '1251792': 0, '264241': 1, '1023461': 0, '363962': 0, '881191': 0, '1205620': 1, '710418': 0, '625701': 0, '666071': 1, '1240011': 0, '118266': 0, '656568': 0, '119234': 1, '733179': 1, '715927': 0, '628593': 0, '522555': 0, '124987': 1, '114679': 1, '167737': 0, '697516': 1, '1103878': 1, '1168334': 0, '108293': 1, '466737': 0, '913725': 1, '661076': 1, '716241': 0, '591727': 1, '166253': 0, '794385': 1, '689538': 1, '892851': 0, '201541': 0, '1112340': 0, '1016480': 0, '498302': 0, '1164996': 0, '129789': 1, '578448': 0, '5659': 0, '1084892': 0, '608660': 0, '632138': 1, '311539': 0, '222400': 1, '1129151': 1, '736625': 0, '555901': 1, '458142': 1, '69959': 1, '543589': 0, '550905': 0, '429418': 0, '359740': 1, '368359': 0, '500197': 1, '17313': 1, '615413': 1, '981889': 1, '1087681': 0, '806406': 0, '118463': 1, '818832': 1, '1015225': 1, '171607': 0, '898967': 0, '677457': 0, '67818': 1, '791238': 1, '971827': 1, '1034469': 0, '1148615': 1, '561224': 0, '503464': 1, '1014453': 1, '1168795': 0, '81755': 1, '690311': 1, '106960': 0, '145501': 1, '133092': 0, '499267': 0, '611505': 1, '241146': 1, '616301': 0, '862323': 0, '564452': 1, '27990': 1, '577786': 0, '963288': 0, '699894': 0, '866081': 1, '1011679': 1, '712061': 1, '992776': 0, '1075547': 0, '162608': 0, '349632': 1, '1084302': 0, '217132': 0, '1051178': 0, '772295': 1, '7557': 1, '1126699': 1, '92220': 1, '805144': 0, '564311': 0, '804004': 0, '480560': 1, '243562': 0, '1198969': 0, '422316': 0, '287501': 0, '287118': 0, '230469': 1, '1077868': 0, '13768': 0, '596447': 1, '402391': 1, '1127975': 0, '1088020': 0, '441383': 0, '1085542': 1, '999083': 0, '32274': 0, '1252091': 1, '40111': 1, '875391': 0, '973351': 0, '222449': 1, '272191': 0, '352610': 0, '531103': 1, '92969': 1, '1201152': 1, '346831': 1, '183946': 0, '739136': 1, '835583': 0, '1005527': 1, '1136395': 0, '147274': 0, '620428': 1, '832774': 1, '43426': 0, '875892': 0, '624169': 0, '333754': 0, '263677': 1, '836918': 1, '121569': 1, '153443': 1, '499116': 0, '707730': 0, '77305': 1, '971700': 0, '206249': 0, '462721': 0, '826467': 0, '296551': 0, '683413': 1, '548704': 1, '396281': 1, '999587': 1, '111937': 0, '383120': 1, '738184': 0, '1103699': 0, '779482': 1, '67745': 0, '270658': 1, '1161185': 1, '105492': 0, '300335': 0, '847491': 1, '323064': 0, '846041': 0, '1191555': 1, '1240871': 0, '879446': 1, '130501': 1, '281051': 1, '303058': 1, '1024563': 1, '492': 1, '261321': 1, '271873': 1, '301256': 1, '1047995': 0, '281358': 0, '460606': 0, '820034': 1, '10831': 0, '563480': 0, '420423': 0, '694601': 0, '290593': 0, '1007602': 0, '14847': 1, '990891': 0, '118851': 1, '1160243': 0, '58149': 0, '889606': 1, '478597': 1, '935990': 1, '131574': 0, '449784': 0, '1158875': 1, '1128563': 1, '201739': 1, '1228651': 0, '260123': 0, '854853': 0, '483604': 0, '961489': 0, '865038': 1, '952208': 1, '155903': 0, '655576': 0, '865522': 0, '169164': 0, '643393': 0, '291951': 0, '181257': 1, '354249': 1, '798364': 1, '950722': 0, '1189047': 0, '655398': 1, '117403': 0, '935809': 0, '1188767': 0, '429476': 1, '947772': 0, '175354': 1, '1211940': 0, '1124740': 0, '347287': 1, '833615': 0, '8805': 1, '888192': 0, '28577': 0, '910341': 1, '853326': 0, '798805': 0, '302558': 0, '132270': 0, '938227': 1, '563257': 1, '43998': 1, '1033074': 0, '749133': 0, '914556': 0, '50356': 1, '702651': 1, '104152': 0, '199045': 1, '359903': 0, '58761': 0, '270903': 0, '846291': 1, '1152555': 0, '242190': 0, '607882': 0, '1250799': 1, '1059037': 1, '211715': 1, '303862': 1, '183376': 1, '1093023': 0, '754387': 0, '857781': 1, '260754': 0, '811631': 1, '461454': 1, '109449': 0, '766691': 1, '987729': 1, '65514': 0, '39918': 0, '41911': 0, '1094278': 0, '634123': 0, '4343': 0, '824194': 0, '26747': 0, '70377': 0, '263038': 1, '534534': 1, '102531': 0, '103750': 1, '508560': 1, '425224': 0, '749957': 1, '662693': 1, '891319': 1, '946194': 0, '91323': 0, '848875': 0, '713091': 1, '50285': 0, '954803': 1, '418112': 1, '245517': 1, '254666': 0, '905732': 0, '521938': 0, '1128469': 1, '478143': 1, '299803': 0, '369714': 1, '1229926': 1, '634225': 0, '926491': 1, '1032655': 1, '873503': 1, '403886': 0, '126736': 0, '921111': 1, '1232131': 1, '963891': 1, '1006900': 0, '772513': 0, '863321': 0, '691047': 0, '555222': 0, '320459': 1, '1194649': 1, '1169431': 0, '355330': 0, '72522': 1, '192123': 0, '196055': 1, '286185': 1, '637195': 0, '837565': 1, '114013': 1, '684214': 0, '32690': 0, '624574': 1, '450174': 0, '833167': 0, '187416': 0, '308428': 0, '157542': 1, '740800': 1, '583135': 0, '120451': 0, '159795': 1, '585564': 0, '311462': 1, '904731': 0, '998355': 1, '1144388': 0, '84322': 0, '929657': 1, '1192363': 0, '967869': 1, '430811': 1, '943523': 1, '116572': 1, '529566': 0, '523732': 1, '1180129': 0, '306105': 1, '1077928': 1, '438627': 1, '1098525': 0, '96072': 0, '1046789': 0, '695214': 1, '902926': 1, '1179799': 0, '976284': 1, '1038338': 1, '302563': 0, '528051': 0, '926586': 0, '130607': 0, '627892': 0, '319002': 1, '179845': 0, '460853': 0, '226563': 0, '136732': 0, '835484': 0, '1020977': 0, '578856': 0, '4901': 1, '1164128': 0, '192895': 1, '175029': 1, '99949': 0, '951920': 1, '1121756': 1, '912132': 1, '1124803': 1, '344912': 0, '1065694': 0, '1040126': 1, '870410': 0, '1053971': 1, '1208174': 1, '476874': 0, '215026': 0, '547023': 0, '863881': 1, '17010': 1, '908908': 0, '280687': 0, '320396': 0, '1125174': 1, '1049013': 0, '251509': 1, '828788': 1, '859577': 0, '1196446': 0, '28228': 1, '1177144': 1, '349270': 1, '1108425': 1, '27555': 1, '973023': 0, '2218': 0, '1052670': 1, '460366': 0, '1179135': 0, '300212': 0, '920261': 1, '501351': 0, '709863': 0, '868200': 1, '370109': 0, '191612': 1, '703841': 1, '916343': 1, '793067': 1, '270695': 0, '172086': 0, '794728': 0, '839707': 1, '21462': 1, '635618': 0, '758530': 1, '24473': 0, '128174': 1, '596381': 1, '593638': 1, '829404': 1, '563089': 1, '69589': 1, '952564': 0, '587757': 1, '1033444': 0, '823479': 1, '358747': 1, '771947': 0, '877710': 0, '911623': 1, '877235': 1, '808250': 1, '757814': 0, '299025': 1, '1158143': 0, '862950': 1, '1137176': 0, '35800': 0, '804061': 1, '996252': 1, '938909': 0, '128853': 0, '603203': 1, '68301': 1, '1200197': 0, '511239': 0, '415888': 1, '142229': 1, '913629': 1, '532763': 1, '1065077': 0, '608463': 1, '961393': 0, '655319': 1, '93690': 1, '123863': 0, '37806': 1, '408123': 0, '423744': 0, '645391': 1, '908875': 1, '328246': 1, '665432': 1, '222784': 1, '1069925': 1, '1124505': 0, '420541': 1, '1148583': 0, '202167': 1, '466028': 1, '942474': 1, '470105': 1, '1184571': 1, '614992': 0, '1212428': 0, '1036494': 0, '122564': 0, '935463': 0, '434431': 0, '1017538': 0, '1053110': 1, '1228859': 1, '836659': 1, '681762': 0, '217241': 1, '1062286': 0, '297348': 1, '606980': 0, '498768': 0, '1069394': 1, '221220': 0, '300052': 1, '804563': 0, '539137': 0, '226856': 0, '863731': 0, '781835': 1, '682499': 0, '1244699': 1, '99784': 0, '938017': 0, '1218008': 0, '1122256': 1, '90344': 0, '805467': 1, '858729': 0, '357355': 1, '260099': 1, '974076': 0, '790668': 0, '242481': 1, '368761': 0, '442370': 1, '582234': 1, '827201': 0, '839916': 1, '1033809': 0, '804419': 0, '1256141': 0, '253808': 0, '35956': 0, '1148848': 1, '1209286': 1, '790186': 0, '432831': 1, '721304': 1, '1207434': 1, '621046': 0, '475896': 1, '411127': 1, '1209264': 1, '783407': 0, '229923': 1, '694197': 1, '813245': 1, '347829': 0, '795370': 0, '1233309': 1, '763250': 0, '899200': 1, '289682': 1, '566637': 1, '33452': 0, '1159527': 0, '1218795': 0, '772003': 1, '220174': 0, '891058': 0, '1097358': 0, '39054': 0, '491512': 1, '363104': 1, '594217': 0, '687334': 1, '784168': 0, '545307': 1, '917534': 0, '109516': 0, '543450': 1, '964452': 0, '222376': 1, '266070': 1, '108748': 1, '71859': 0, '842579': 1, '1149394': 1, '605732': 0, '343783': 1, '709450': 1, '337038': 1, '1115363': 1, '545671': 1, '565463': 1, '155302': 1, '1014386': 0, '830147': 1, '1213440': 1, '859881': 0, '607960': 0, '581522': 0, '849134': 0, '52953': 0, '821398': 0, '284758': 0, '481968': 1, '863706': 0, '641932': 1, '822069': 1, '798156': 1, '1193518': 1, '512309': 1, '1223014': 0, '74096': 1, '14466': 0, '225253': 0, '548791': 0, '814405': 1, '1083721': 1, '2390': 1, '216502': 0, '156524': 0, '1140774': 1, '623031': 1, '17027': 1, '502157': 1, '337659': 0, '937973': 0, '1099173': 0, '1184397': 0, '9264': 1, '270107': 1, '1125430': 1, '644488': 0, '40536': 0, '825469': 1, '715847': 0, '902691': 1, '385768': 0, '391799': 1, '70177': 1, '300616': 1, '1240978': 1, '1077188': 0, '831229': 0, '830973': 0, '189666': 1, '25807': 1, '139643': 0, '909712': 1, '792824': 1, '351189': 0, '761737': 0, '231738': 0, '326668': 0, '27981': 1, '564623': 0, '920453': 0, '577026': 0, '35297': 0, '197318': 1, '1224903': 0, '511335': 0, '457264': 1, '338875': 0, '1147437': 0, '1019477': 1, '1025308': 0, '199448': 0, '73678': 0, '443077': 0, '517920': 1, '425444': 1, '1146744': 0, '386346': 0, '1118313': 0, '1028035': 1, '612120': 0, '548456': 0, '1052938': 0, '480571': 1, '26908': 1, '114569': 1, '1036259': 1, '1025283': 1, '927498': 1, '447828': 0, '1041517': 1, '701725': 1, '505784': 1, '988201': 1, '327748': 0, '1094777': 1, '358887': 0, '782600': 0, '230807': 0, '406404': 1, '914015': 0, '1245216': 0, '974173': 0, '275176': 0, '1070674': 0, '929023': 0, '925105': 1, '106229': 0, '424951': 0, '191734': 1, '502775': 1, '1092355': 1, '78579': 1, '528492': 1, '593171': 0, '54362': 0, '460126': 1, '1229407': 0, '1022012': 0, '1199411': 0, '466743': 1, '382317': 0, '800860': 0, '825136': 0, '108793': 0, '333172': 1, '463412': 0, '396602': 0, '1148501': 0, '344094': 0, '953209': 1, '567426': 0, '660658': 1, '323534': 1, '640241': 0, '109723': 0, '2587': 0, '121275': 0, '870286': 1, '550184': 1, '949624': 0, '1229042': 0, '97821': 0, '408972': 1, '403658': 1, '1127391': 1, '646375': 1, '254906': 1, '180985': 0, '858448': 1, '1046739': 0, '167177': 0, '482748': 1, '236502': 1, '645372': 1, '318952': 0, '784992': 0, '964836': 1, '284241': 0, '1021262': 1, '349558': 1, '77946': 1, '287847': 1, '627070': 1, '503359': 0, '820462': 1, '595478': 1, '173219': 0, '742117': 1, '228286': 1, '812278': 1, '764840': 0, '1161358': 0, '278686': 1, '978252': 0, '737103': 1, '741647': 0, '99473': 1, '678956': 1, '1014411': 1, '589544': 1, '254997': 1, '907319': 1, '1086209': 0, '281067': 1, '568008': 0, '8480': 1, '1142528': 0, '520503': 1}


	testData = {'630898': 1, '881106': 0, '550184': 1, '926586': 0, '480571': 1, '935990': 1, '987729': 1, '817463': 0, '1094882': 0, '492846': 0, '250551': 0, '988201': 1, '740800': 1, '1126083': 0, '1084872': 0, '1087681': 0, '275176': 0, '660441': 1, '352141': 0, '118463': 1, '1216214': 0, '529566': 0, '254666': 0, '422316': 0, '114679': 1, '478143': 1, '683413': 1, '610329': 1, '1233309': 1, '1168334': 0, '254997': 1, '1256666': 1, '1074248': 1, '1201458': 1, '128405': 0, '483604': 0, '1252623': 1, '216502': 0, '873327': 0}
	runCfier(data, testData, sys.argv[1], sys.argv[2])
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
