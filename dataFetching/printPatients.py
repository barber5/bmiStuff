import sys,os, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))

from readIcd9Patients import getInput, binConditionsByAge, selectByAge, binnedTransform, binnedWithCodes, loadCodes
from cohortStats import conditionFrequencies


def printPat(codeFile, patientFile):
	codes = loadCodes(codeFile)
	patients = getInput(patientFile)	
	return patients

if __name__ == "__main__":
	p = printPat(sys.argv[1], sys.argv[2])
	pprint.pprint(p)