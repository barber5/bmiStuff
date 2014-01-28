from autismClusters import getInput, loadCodes, conditionsBinnedYear, condDictsForAges
import sys, pprint

def beforeAfter(patients, before, after):
	count = 0
	for pid, patient in patients.iteritems():
		beforeMin = float('inf')
		afterMin = float('inf')
		afterArr = after.split(',')
		for offset, visit in patient.iteritems():
			for cond in visit['conditions']:
				if cond == before and offset < beforeMin:
					beforeMin = offset
				if offset < afterMin:
					for a in afterArr:
						if cond.find(a) == 0:
							afterMin = offset
		if afterMin < float('inf') and beforeMin < afterMin:
			count += 1
	return float(count) / len(patients)

def filterPatients(patients, reqs):
	filtered = {}
	for pid, patient in patients.iteritems():
		reqDict = {}
		for req in reqs:
			reqDict[req] = False
		for offset, visit in patient.iteritems():
			for cond in visit['conditions']:
				if cond in reqDict:
					reqDict[cond] = True
		foundAll = True
		for req in reqs:
			if not reqDict[req]:
				foundAll = False
				break
		if foundAll:
			filtered[pid] = patient
	return filtered

if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])			
	filtered = filterPatients(patients, sys.argv[5:])
	print beforeAfter(filtered, sys.argv[3], sys.argv[4])
	print len(filtered)