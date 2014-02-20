import sys,os, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))

from readIcd9Patients import getInput, binConditionsByAge, selectByAge, binnedTransform, binnedWithCodes, loadCodes
from cohortStats import conditionFrequencies



def missingCodes(codeFile, patientFile, code):
	codes = loadCodes(codeFile)
	patients = getInput(patientFile)		
	binnedPat = binConditionsByAge(patients)	
	selectedPat = selectByAge(binnedPat, 0, 100)		
	codedPat = binnedWithCodes(selectedPat, codes)
	missing = []
	for pat, conds in codedPat.iteritems():
		foundIt = False
		for cond, freq in conds.iteritems():
			if cond == code:
				foundIt = True
				break
		if not foundIt:
			missing.append((pat,patients[pat]))
	return missing

if __name__ == "__main__":
	m = missingCodes(sys.argv[1], sys.argv[2], sys.argv[3])
	pprint.pprint(m)