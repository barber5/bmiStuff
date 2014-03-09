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

	# for each in training, predict with our mod and see if we're right or not
	# calculate stats and see what the news is

	None

if __name__ == "__main__":
	data = {'1221000': 0, '73012': 1, '1164347': 0, '45743': 1, '363962': 0, '384067': 0, '1065445': 0, '125075': 1, '1112340': 0, '366230': 0, '268582': 0, '317764': 0, '429418': 0, '131448': 1, '1240871': 0, '177389': 1, '1251792': 0, '581601': 1, '365800': 1, '469277': 1, '294923': 1, '926586': 0, '698102': 1, '625701': 0, '1241748': 1, '1240011': 0, '1194058': 1, '71161': 0, '576639': 1, '554397': 0, '543589': 0, '628593': 0, '214096': 1, '708022': 0, '996270': 1, '306743': 1, '184538': 1, '653716': 0, '1169442': 1, '300394': 1, '835484': 0, '978496': 0, '764501': 0, '495774': 0, '716241': 0, '458700': 1, '1072076': 0, '173159': 0, '82618': 1, '1214055': 0, '463869': 0, '1093023': 0, '1016480': 0, '498302': 0, '677782': 1, '273428': 1, '330405': 1, '270': 0, '999147': 0, '659373': 1, '311539': 0, '987947': 1, '673971': 0, '518954': 1, '220694': 0, '531998': 1, '873624': 1, '323057': 1, '1112077': 1, '1175529': 1, '223036': 0, '136732': 0, '1136907': 0, '1165452': 1, '1233972': 0, '416411': 0, '755810': 0, '1121675': 0, '328543': 1, '1232108': 0, '46262': 1, '1140029': 0, '1216214': 0, '869336': 0, '1009430': 1, '27905': 1, '453847': 1, '614992': 0, '563607': 1, '561224': 0, '606783': 1, '266821': 1, '577869': 0, '476715': 1, '878681': 0, '21195': 0, '154273': 1, '225589': 1, '242449': 1, '151373': 0, '1219342': 1, '903072': 0, '696942': 1, '256262': 0, '616301': 0, '797316': 1, '1112389': 1, '577396': 1, '1112228': 1, '841543': 0, '88440': 0, '374680': 1, '211551': 1, '311054': 1, '370283': 1, '1022917': 1, '217132': 0, '406249': 0, '1126913': 1, '145371': 1, '1037726': 1, '215589': 0, '243562': 0, '19337': 1, '239310': 1, '590460': 1, '287118': 0, '1027018': 1, '819107': 0, '1099093': 1, '856072': 1, '1126254': 1, '735334': 1, '720826': 1, '352610': 0, '120768': 1, '230743': 1, '226151': 1, '448520': 1, '799157': 1, '772068': 1, '239861': 0, '683303': 1, '132884': 0, '466679': 1, '272191': 0, '987543': 0, '915608': 1, '954466': 0, '332581': 0, '752878': 1, '183946': 0, '564623': 0, '369220': 1, '912644': 0, '824821': 1, '835583': 0, '395556': 1, '733504': 1, '458690': 1, '945067': 0, '1056618': 1, '116646': 1, '927125': 0, '499116': 0, '1049021': 0, '606466': 1, '378968': 0, '176765': 1, '224733': 0, '971700': 0, '260754': 0, '1185118': 1, '373469': 1, '6030': 1, '300335': 0, '1134740': 1, '200743': 0, '200741': 1, '1251712': 0, '1047690': 0, '212761': 1, '1116805': 1, '946989': 0, '195928': 1, '119121': 1, '501351': 0, '256455': 1, '1124300': 1, '472566': 1, '1136395': 0, '160815': 0, '146056': 1, '683488': 0, '330692': 1, '890379': 0, '265072': 1, '318420': 1, '812468': 1, '99784': 0, '420423': 0, '827201': 0, '290593': 0, '1132875': 1, '1160081': 0, '1160243': 0, '296177': 1, '1209249': 1, '900602': 1, '800113': 1, '507556': 0, '557760': 0, '635604': 0, '460853': 0, '51273': 1, '255682': 1, '149486': 1, '41305': 0, '48212': 1, '155903': 0, '553520': 0, '698116': 1, '276051': 0, '612950': 0, '978293': 1, '346898': 1, '25059': 0, '736089': 1, '1094278': 0, '749147': 1, '3305': 1, '1035196': 1, '211763': 0, '933338': 0, '1222873': 0, '226450': 1, '480801': 1, '833615': 0, '978252': 0, '812976': 0, '543508': 1, '902951': 1, '1059319': 1, '1113362': 1, '798805': 0, '511432': 0, '817281': 1, '618762': 1, '352141': 0, '487131': 1, '973490': 0, '332876': 1, '989105': 0, '1047358': 1, '974076': 0, '1214335': 0, '541515': 1, '1051848': 1, '607882': 0, '627603': 1, '754387': 0, '901851': 1, '454790': 0, '293758': 1, '577255': 1, '488136': 0, '1236043': 0, '389828': 0, '1065273': 1, '409101': 0, '392050': 1, '905415': 1, '83017': 1, '492846': 0, '946937': 1, '167050': 1, '969177': 1, '688422': 1, '523695': 1, '355705': 1, '102531': 0, '473570': 1, '201391': 0, '985422': 1, '861501': 1, '359870': 0, '174559': 0, '403886': 0, '50285': 0, '2623': 0, '716284': 0, '1252221': 1, '249997': 1, '267060': 1, '905732': 0, '566169': 1, '974173': 0, '521938': 0, '1020977': 0, '897591': 0, '738214': 1, '1019553': 0, '291422': 1, '995062': 1, '1114994': 1, '247157': 1, '660151': 1, '91256': 0, '1127621': 0, '768997': 1, '977660': 1, '35800': 0, '691047': 0, '144819': 0, '48030': 0, '95913': 0, '431750': 1, '118863': 1, '383680': 0, '291629': 0, '134708': 0, '1249871': 1, '670821': 0, '682499': 0, '317396': 0, '682625': 1, '973061': 1, '61081': 0, '645782': 0, '223833': 0, '60876': 1, '715847': 0, '1109060': 0, '613726': 1, '790581': 0, '903817': 1, '1170462': 1, '1082771': 0, '147990': 1, '860032': 0, '904731': 0, '76361': 1, '88071': 0, '420355': 0, '982247': 1, '632782': 1, '241473': 0, '829131': 1, '220174': 0, '1053437': 1, '307334': 0, '166379': 1, '572355': 0, '199002': 1, '1098525': 0, '107779': 1, '550905': 0, '776737': 0, '908535': 0, '648397': 1, '578870': 1, '124276': 1, '347036': 1, '49538': 1, '229344': 0, '671344': 1, '179845': 0, '350547': 0, '6007': 0, '453682': 1, '75490': 0, '1117301': 1, '1164128': 0, '140309': 1, '1255512': 1, '917534': 0, '524995': 1, '188421': 1, '494998': 0, '879105': 1, '618512': 0, '1181776': 1, '476874': 0, '116623': 0, '447095': 0, '713032': 1, '847506': 1, '280687': 0, '987817': 1, '1080205': 1, '456704': 0, '525003': 1, '633731': 0, '518114': 1, '1238711': 1, '158066': 1, '351551': 0, '861478': 1, '1179135': 0, '946194': 0, '1091465': 1, '136249': 1, '68013': 0, '723867': 1, '637318': 1, '563572': 1, '1021421': 1, '434008': 1, '683625': 1, '396602': 0, '84322': 0, '793528': 1, '629321': 0, '965607': 1, '26825': 0, '1030245': 1, '1233816': 0, '320396': 0, '1107798': 1, '1081245': 1, '522929': 1, '1033444': 0, '1084302': 0, '511790': 0, '1169540': 1, '628043': 1, '1158143': 0, '783407': 0, '122564': 0, '105492': 0, '1200197': 0, '1021332': 1, '637222': 1, '1124026': 0, '601270': 0, '1190326': 1, '10866': 1, '1017447': 1, '537188': 1, '25134': 1, '585449': 1, '863321': 0, '1174552': 1, '881106': 0, '78991': 1, '753834': 1, '1124505': 0, '702997': 1, '807947': 1, '150598': 0, '226637': 1, '964998': 1, '673618': 1, '401359': 1, '191510': 0, '962269': 0, '1212428': 0, '1089792': 0, '1077219': 1, '929023': 0, '79186': 1, '111002': 0, '487665': 0, '876156': 0, '1017538': 0, '2587': 0, '857849': 0, '86869': 0, '646269': 0, '205403': 0, '440818': 1, '518137': 0, '35885': 0, '851287': 1, '580806': 1, '17690': 1, '588770': 1, '321514': 1, '1042914': 1, '918502': 0, '788158': 0, '1078979': 1, '383439': 1, '1006224': 1, '168068': 1, '90344': 0, '936311': 1, '125466': 0, '423017': 0, '96715': 1, '313418': 1, '1024625': 1, '1135035': 0, '650946': 1, '973502': 1, '684214': 0, '708096': 0, '764828': 0, '568396': 1, '480165': 0, '911246': 1, '1056093': 0, '835474': 1, '319315': 0, '666426': 0, '194069': 0, '127860': 0, '661799': 1, '1169257': 0, '130984': 0, '21413': 1, '687680': 1, '255275': 1, '549367': 0, '1000379': 1, '1104280': 1, '833167': 0, '33452': 0, '446849': 1, '604895': 1, '855285': 0, '467782': 0, '528051': 0, '520817': 1, '698769': 1, '32708': 0, '555961': 1, '109512': 0, '7117': 1, '101484': 1, '71859': 0, '363097': 0, '532097': 1, '75555': 1, '477545': 0, '709668': 0, '52953': 0, '1093133': 0, '367910': 1, '320945': 1, '483586': 1, '396737': 1, '1082837': 1, '405015': 1, '859881': 0, '849134': 0, '157903': 1, '756191': 0, '1137489': 0, '966217': 0, '753613': 0, '736777': 0, '320497': 0, '1068639': 1, '116700': 1, '39373': 0, '177207': 1, '1032053': 1, '1180067': 0, '260123': 0, '1039148': 0, '355616': 1, '1074005': 0, '1088463': 1, '1242774': 1, '153043': 1, '600017': 1, '284273': 0, '156524': 0, '831175': 0, '147139': 1, '603420': 1, '152709': 1, '749133': 0, '190050': 1, '771536': 0, '805826': 0, '644488': 0, '778229': 1, '267189': 1, '1035216': 1, '446062': 0, '549526': 1, '1195515': 1, '975106': 1, '359914': 1, '957938': 1, '133953': 1, '1219941': 0, '821014': 0, '1077188': 0, '513416': 1, '31101': 1, '96789': 1, '896083': 1, '139643': 0, '1196534': 0, '85627': 0, '341977': 0, '737386': 1, '820760': 0, '992776': 0, '715479': 1, '827851': 1, '446600': 1, '919780': 0, '587294': 0, '520716': 1, '1103198': 1, '35297': 0, '1057183': 1, '1224903': 0, '53879': 0, '698546': 1, '222659': 1, '544519': 0, '259850': 1, '1222608': 1, '924554': 1, '1045864': 1, '206536': 1, '128187': 0, '1103699': 0, '443077': 0, '655556': 1, '556180': 1, '271135': 1, '708548': 1, '1118313': 0, '1101749': 1, '379144': 0, '384140': 1, '1174396': 1, '536187': 1, '504658': 0, '1046193': 0, '921604': 1, '562252': 1, '984654': 1, '358887': 0, '142621': 1, '1206489': 1, '786394': 1, '253709': 0, '84612': 1, '1228012': 1, '1179799': 0, '487478': 0, '70495': 1, '279881': 1, '82489': 1, '480406': 1, '421752': 1, '83341': 1, '424951': 0, '56663': 1, '1058060': 1, '1089454': 0, '832160': 1, '1146068': 0, '1004859': 0, '138913': 0, '1127424': 0, '949078': 1, '186821': 0, '1229407': 0, '382317': 0, '633872': 1, '1140739': 1, '416811': 0, '300212': 0, '724549': 1, '3370': 1, '333625': 1, '1148501': 0, '849451': 1, '929031': 1, '621554': 1, '1166113': 0, '97198': 1, '109723': 0, '790754': 1, '902308': 1, '334284': 1, '63078': 1, '767403': 1, '822859': 1, '670065': 1, '105293': 0, '255719': 0, '175959': 1, '358221': 0, '345824': 1, '738184': 0, '940639': 1, '167177': 0, '1087681': 0, '387246': 1, '858729': 0, '777958': 0, '502573': 1, '955653': 1, '484938': 0, '293636': 1, '944245': 0, '1151728': 1, '1206183': 0, '764840': 0, '136562': 1, '1123648': 0, '350209': 1, '1204037': 1, '522327': 1, '835926': 1, '422316': 0, '621824': 1, '1014413': 0, '272795': 0, '234317': 1, '534586': 1, '1061101': 0, '373427': 1, '820344': 1}

	testData = {'35234': 1, '124276': 1, '627892': 0, '1254744': 1, '711306': 0, '827210': 1, '810451': 1, '869342': 0, '794728': 0, '955271': 0, '145684': 0, '625701': 0, '284758': 0, '950735': 1, '1192589': 1, '124479': 0, '589688': 1, '1134740': 1, '1069058': 1, '300090': 1, '149486': 1, '633731': 0, '962176': 1, '513542': 1, '1016480': 0, '1179135': 0, '509240': 0, '1190485': 1, '40536': 0, '167108': 1, '236274': 1, '997864': 1, '468953': 1, '416411': 0, '800079': 1, '510751': 1, '552819': 0, '835474': 1, '1219812': 0, '175369': 1, '531314': 1, '643393': 0, '1045864': 1, '1155442': 1, '95913': 0, '25134': 1, '109449': 0, '389828': 0, '290464': 1, '227968': 0, '1135700': 0, '182731': 1, '617320': 0, '358887': 0, '318662': 0, '766265': 1, '1036494': 0, '991561': 1, '57064': 1, '387340': 0, '371684': 1, '949078': 1, '355330': 0, '915182': 1, '220694': 0, '525676': 1, '567426': 0, '234470': 1, '492759': 1, '619634': 0, '451041': 1, '1178234': 0, '17690': 1, '175959': 1, '817463': 0, '317396': 0, '545769': 1, '1026496': 1, '603492': 1, '253197': 0, '239861': 0, '221801': 1, '120451': 0, '839407': 0, '1191314': 0, '651620': 0, '462721': 0, '146901': 1, '1155008': 1, '1239244': 1, '530940': 0, '1086209': 0, '808915': 1, '975393': 0, '1061808': 0, '1179799': 0, '136161': 0, '855285': 0}
	runCfier(data, testData)
	



'''
The plan is to have as input a set of training and test data which are basically pids/labels in each file

We read in the pids 

We then grab the feature vectors (first check cache, if not, load from datastore)  #TODO: need to figure out whether to take the whole patient or the patient up til some point in time (maybe visit right before the diagnosis???)

Use the dictvectorizer or something else and train a l1 regularized cfier -- save random forests for big jump?



'''
