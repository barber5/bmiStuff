import sys, pprint
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import KernelPCA
from sklearn.cluster import DBSCAN as cluster
import re


blacklist = set(['299.00', '783.40', '315.9', '299.80', '783.42', '299.90', 'V20.2', 'V79.3', 'V72.6', '88.91', 'V70.7'])

def getInput(fileName):
	patients = {}
	with open(fileName, 'r') as fi:
		while True:
			line = fi.readline()
			if line == '':
				break
			lineArr = line.strip().split('\t')			
			record = {
				'id': lineArr[0],
				'age': int(lineArr[1]),
				'offset': float(lineArr[2]),
				'year': lineArr[3],
				'conditions': []			
			}
			if len(lineArr) > 4:
				record['conditions'] = lineArr[4].split(',')
			if record['id'] not in patients:
				patients[record['id']] = {}
			if record['offset'] not in patients[record['id']]:
				patients[record['id']][record['offset']] = record
		fi.close()
	return patients

def minOffsetForPatient(patient):
	minOffset = float("inf")
	diagAge = -1
	codes = {}
	# find first autism code
	for offset in patient:			
		visit = patient[offset]				
		age = visit['age']
		for condition in visit['conditions']:
			if condition not in codes:
				codes[condition] = True
			if condition == '299.00' or condition == '299.01':				
				if offset < minOffset:
					minOffset = offset
					diagAge = age
	return diagAge, minOffset

def firstDiag(patients):
	diagAges = []
	diagVisits = []
	for pid in patients:		
		patient = patients[pid]		
		diagAge, minOffset = minOffsetForPatient(patient)
		# visits before, after -- minOffset contains first diagnosis from last loop
		if minOffset == float("inf"):
			continue
		diagAges.append(diagAge)
	return diagAges

def conditionsBinnedYear(patients, filterFlag=False):
	patientConds = {}
	for pid, patient in patients.iteritems():		
		minOffset = minOffsetForPatient(patient)
		if minOffset == float("inf"):
			continue
		if pid not in patientConds:
			patientConds[pid] = {}
		for offset, visit in patient.iteritems():
			age = visit['age']
			if age not in patientConds[pid]:
				patientConds[pid][age] = {}
			for cond in visit['conditions']:	
				if filterFlag and cond in blacklist:
					continue
				if cond[0] == 'V':
					continue
				if cond not in patientConds[pid][age]:
					patientConds[pid][age][cond] = 0
				patientConds[pid][age][cond] += 1
	return patientConds

# given some patient conditions as given by e.g. conditionsBinnedYear
# and a vector of ages construct vectors for patients
def condDictsForAges(patientConds, ageVec, countFrequencies=True):
	patientCondSets = {}
	for pid, ages in patientConds.iteritems():
		conds = {}
		for age in ageVec:			
			if age not in ages:
				continue
			for cond in ages[age]:
				if cond not in conds:
					if countFrequencies:
						conds[cond] = 0
					else:
						conds[cond] = 1

				if countFrequencies:
					conds[cond] += ages[age][cond]			
		if len(conds) == 0:
			continue
		patientCondSets[pid] = conds
	return patientCondSets

def clusterConditionsByAge(patientConds, lo, hi, collapse=False, countFrequencies=True):	
	ageVec = range(lo, hi+1)
	patientCondDicts = condDictsForAges(patientConds, ageVec, countFrequencies)
	patientFeatures = {}
	measurements = []
	pidIndexer = {}
	i=0
	for patient, conds in patientCondDicts.iteritems():		
		if collapse:
			newConds = {}
			for cond in conds:
				count = conds[cond]
				if cond.find('.') != -1:
					cond = cond.split('.')[0]
				if cond not in newConds:
					if countFrequencies:
						newConds[cond] = 0
					else:
						newConds[cond] = 1
				if countFrequencies:
					newConds[cond] += count
			conds = newConds
		pidIndexer[i] = patient
		measurements.append(conds)
		i += 1
	vec = DictVectorizer()
	featArray = vec.fit_transform(measurements).toarray()
	tfidf = TfidfTransformer()
	tfidfArray = tfidf.fit_transform(featArray)
	dimReducer = KernelPCA(n_components=300)
	reducedFeatArray = dimReducer.fit_transform(tfidfArray)
	#reducedFeatArray = featArray
	c = cluster(metric='correlation', algorithm='brute', min_samples=10, eps=.2)
	labels = c.fit_predict(reducedFeatArray)	
	clusters = {}
	clusterPatients = {}
	for i, l in enumerate(labels):
		if l == -1:
			continue
		if l not in clusters:
			clusters[l] = []
			clusterPatients[l] = []
		clusters[l].append(i)
		pid = pidIndexer[i]
		condDicts = patientCondDicts[pid]
		clpat = {
			'pid': pid,
			'conditions': condDicts
		}
		clusterPatients[l].append(clpat)
	return clusterPatients

def loadCodes(codeFile):
	codes = {}
	with open(codeFile, 'r') as fi:		
		while True:
			line = fi.readline()
			if line == '':
				break
			lineArr = line.split('\t')
			code = {
				'code': lineArr[0],
				'desc': lineArr[1]
			}
			if re.match(r'V\d', code['code']):
				newCode = code['code'][:3] + '.' + code['code'][3:]
				code['code'] = newCode
			elif re.match(r'\d+', code['code']) and len(code['code']) > 3:				
				newCode = code['code'][:3] + '.' + code['code'][3:]		
				code['code'] = newCode				
			elif re.match(r'\D\d', code['code']) and len(code['code']) > 4:
				newCode = code['code'][:4] + '.' + code['code'][4:]
				code['code'] = newCode				
			codes[code['code']] = code['desc']

		fi.close()
	return codes

def patientClusterCodes(clusterPatients, codes):
	clusterCodes = {}
	for clid, patients in clusterPatients.iteritems():
		clusterCodes[clid] = {}
		for patient in patients:
			for code,cnt in patient.iteritems():
				if code not in clusterCodes[clid]:
					if code not in codes:
						codeDesc = code
					else:
						codeDesc = codes[code]

					clusterCodes[clid][code] = {
						'count': 0,
						'desc': codeDesc,						
					}
				clusterCodes[clid][code]['count'] += cnt
	return clusterCodes

def patientClusterCodesCollapsed(clusterPatients, codes, collapse=False, countFrequencies=True):
	clusterCodes = {}
	for clid, patients in clusterPatients.iteritems():		
		clusterCodes[clid] = {}
		patientCollapse = {}
		for patient in patients:
			collapsedSeen = {}
			for code,cnt in patient['conditions'].iteritems():
				if collapse and code.find('.') != -1:
					collapsed = code.split('.')[0]
				else:
					collapsed = code
				if collapsed not in clusterCodes[clid]:					
					clusterCodes[clid][collapsed] = {
						'count': 0,
						'desc': set([]),						
					}				
				if code not in codes:
					codeDesc = code
				else:
					codeDesc = codes[code]
				if countFrequencies:
					clusterCodes[clid][collapsed]['count'] += cnt	
				elif collapsed not in collapsedSeen:
					collapsedSeen[collapsed] = True
					clusterCodes[clid][collapsed]['count'] += 1
				clusterCodes[clid][collapsed]['desc'].add(code+' '+codeDesc)
		result = {}
		for code, stat in clusterCodes[clid].iteritems():			
			if stat['count'] > 1:
				result[code] = stat
		clusterCodes[clid] = result
		clusterCodes[clid]['zSize'] = len(patients)
		
	return clusterCodes

def clusterFlow(early, late):
	flowDict = {}
	for clu, patients in early.iteritems():
		for patient in patients:
			flowDict[patient['pid']] = {
				'early': clu
			}
	for clu, patients in late.iteritems():
		for patient in patients:
			if patient['pid'] in flowDict:
				flowDict[patient['pid']]['late'] = clu
			else:
				flowDict[patient['pid']] = {
				'late': clu
			}	
	for pid, flow in flowDict.iteritems():
		if 'early' not in flow:
			flow['early'] = -1
		if 'late' not in flow:
			flow['late'] = -1
	return flowDict

def countFlows(flowDict):
	counts = {}
	for pid, flow in flowDict.iteritems():
		early = flow['early'] + 1
		late = flow['late'] + 1
		if (early, late) not in counts:
			counts[(early,late)] = 0
		counts[(early, late)] += 1
	return counts


if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])		
	
	
	patientConds = conditionsBinnedYear(patients, filterFlag=True)
	early = clusterConditionsByAge(patientConds, int(sys.argv[3]), int(sys.argv[4]), False)
	late = 	clusterConditionsByAge(patientConds, int(sys.argv[5]), int(sys.argv[6]), False)

	earlyCodes = patientClusterCodesCollapsed(early, codes, True, False)
	print 'early: {}-{}'.format(sys.argv[3], sys.argv[4])
	pprint.pprint(earlyCodes)
	lateCodes = patientClusterCodesCollapsed(late, codes, True, False)
	print '\n\n\n\nlate: {}-{}'.format(sys.argv[5], sys.argv[6])
	pprint.pprint(lateCodes)

	flowDict = clusterFlow(early, late)
	counts = countFlows(flowDict)
	print '\n\n\n\n\nflows'
	pprint.pprint(counts)
	
	
	

