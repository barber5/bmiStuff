from autismClusters import getInput, loadCodes, conditionsBinnedYear, condDictsForAges
import sys, pprint

def beforeAfter(patients, before, after):
	count = 0
	for pid, patient in patients.iteritems():
		beforeMin = float('inf')
		afterMin = float('inf')
		for offset, visit in patient.iteritems():
			for cond in visit['conditions']:
				if cond == before and offset < beforeMin:
					beforeMin = offset
				if cond == after and offset < afterMin:
					afterMin = offset
		if afterMin < float('inf') and beforeMin < afterMin:
			count += 1
	return float(count) / len(patients)

if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])			
	print beforeAfter(patients, sys.argv[3], sys.argv[4])