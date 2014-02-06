import sys, pprint, re

# intput: filename
# output: {pid -> {offset->{record}}}
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
				record['conditions'] = lineArr[4].strip().split(',')
			if record['id'] not in patients:
				patients[record['id']] = {}
			if record['offset'] not in patients[record['id']]:
				patients[record['id']][record['offset']] = record
			print record
		fi.close()
	return patients

# input: {pid -> {offset->{record}}}
# output: {pid -> {age ->[{cond -> count}]}}
def binConditionsByAge(patients):
	result = {}
	for pid, patient in patients.iteritems():
		if pid not in result:
			result[pid] = {}
			for offset, record in patient.iteritems():
				if record['age'] not in result[pid]:
					result[pid][record['age']] = {}
				for cond in record['conditions']:	
					if cond not in result[pid][record['age']]:
						result[pid][record['age']][cond] = 0
					result[pid][record['age']][cond] += 1								
	return result

# input: {pid -> {age ->[{cond -> count}]}}
# output: {pid -> [{cond -> count}]}
def selectByAge(patients, minAge, maxAge):
	result = {}
	for pid, patient in patients.iteritems():
		if pid not in result:
			result[pid] = {}
		for age, conditions in patient.iteritems():
			if age > minAge and age < maxAge:
				for cond in conditions:
					if cond not in result[pid]:
						result[pid][cond] = 0
					result[pid][cond] += 1
	newResult = {}
	for pid, conds in result.iteritems():
		if len(conds) > 0:
			newResult[pid] = conds
	return newResult

# input: {pid -> {offset -> {record}}}, refpoint is a float or a dict with {pid -> refPoint}
# output: {pid -> {offset ->[{cond -> count}]}}
def binConditionsByOffset(patients, refPoint=0.0):
	result = {}
	for pid, patient in patients.iteritems():
		if pid not in result:
			result[pid] = {}
			for offset, record in patient.iteritems():
				if type(refPoint) == type({}):
					basePoint = refPoint[pid]
				else:
					basePoint = refPoint
				offset = int(str(offset).split('.')[0]) - basePoint
				if offset not in result[pid]:
					result[pid][offset] = {}
				for cond in record['conditions']:								
					if cond not in result[pid][offset]:
						result[pid][offset][cond] = 0
					result[pid][offset][cond] += 1
	
	return result


# input: {pid -> {offset ->[{cond -> count}]}}
# output: {pid -> [{cond -> count}]}
def selectByOffset(patients, minOff, maxOff):
	result = {}
	for pid, patient in patients.iteritems():
		if pid not in result:
			result[pid] = {}
		for offset, conditions in patient.iteritems():
			if offset > minOff and offset < maxOff:
				for cond in conditions:					
					if cond not in result[pid]:
						result[pid][cond] = 0
					result[pid][cond] += 1
	newResult = {}
	for pid, conds in result.iteritems():
		if len(conds) > 0:
			newResult[pid] = conds
	return newResult

# postprocess our vecs, ignore is checked first, then a collapse attempt is made
# applied then normalizing from bags to sets is tried (bernoulli)
# if bernoulli is set then freqThreshold refers to the frequency a condition needs to be seen in the 
# cohort to not get filtered
#
# input: {pid -> [{cond -> count}]
# output {pid -> [{cond -> count}]
def binnedTransform(patients, collapse=False, bernoulli=False, ignore=None, populationFreqThreshold=None, individualFreqThreshold=None):
	result = {}
	conditionsPatientsIdx = {}
	if not collapse and not bernoulli and not ignore and not populationFreqThreshold and not individualFreqThreshold:
		return patients	
	# filter
	for pid, conds in patients.iteritems():			
		if pid not in result:
			result[pid] = {}
		for cond, cc in conds.iteritems():			
			if ignore and cond in ignore:
				continue
			if collapse:
				if cond.find('.') != -1:
					cond = cond.split('.')[0]
			if individualFreqThreshold and cc < individualFreqThreshold:
				continue					
			if cond not in conditionsPatientsIdx:
				conditionsPatientsIdx[cond] = 0
			conditionsPatientsIdx[cond] += 1		
			if bernoulli:
				cc = 1			
			result[pid][cond] = cc
	newResult = {}
	for pid, conds in result.iteritems():		
		if populationFreqThreshold:
			newConds = {}
			for cond,cc in conds.iteritems():
				if float(conditionsPatientsIdx[cond]) / len(patients) > populationFreqThreshold:
					newConds[cond] = cc
			conds = newConds		
		if len(conds) == 0:
			continue
		newResult[pid] = conds
	return newResult

# intput: filename
# output: {code -> desc}
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
			if code['code'].find('.') != -1:
				codeWhole = code['code'].split('.')[0]
				if codeWhole not in codes:
					codes[codeWhole] = 'Composite:'
				codes[codeWhole] += ' {}: {}'.format(code['code'], code['desc'])
		fi.close()
	return codes				

# was doing something else here, could use a defaultdict now instead
def codeLookup(codes, query):
	if str(query) in codes:
		return codes[query]
	else:
		return ''

# input: {pid -> [{cond -> count}]
# output: {pid -> [{cond -> {count, desc}}]}
def binnedWithCodes(patients, codes):
	result = {}
	for pid, patient in patients.iteritems():
		result[pid] = {}
		for cond,cnt in patient.iteritems():
			desc = codeLookup(codes, cond)
			result[pid][cond] = {
				'count': cnt,
				'desc': unicode(desc, errors='ignore')
			}
	return result

if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])
	binned = binConditionsByAge(patients)
	selected = selectByAge(binned, int(sys.argv[3]), int(sys.argv[4]))
	xformed = binnedTransform(selected, collapse=True, populationFreqThreshold=.2)
	coded = binnedWithCodes(xformed, codes)
	pprint.pprint(coded)

