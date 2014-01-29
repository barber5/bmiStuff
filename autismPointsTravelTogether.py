from autismClusters import getInput, loadCodes, conditionsBinnedYear, condDictsForAges
import sys, pprint


if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])		
	patientConds = conditionsBinnedYear(patients)
	pprint.pprint(patientConds)
