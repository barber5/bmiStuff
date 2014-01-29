from autismCodeCounter import patientsWithout
from autismClusters import getInput, loadCodes, conditionsBinnedYear
import sys, pprint


if __name__ == "__main__":
	patients = getInput(sys.argv[1])	
	patientConds = conditionsBinnedYear(patients)
	without = patientsWithout(patientConds, sys.argv[2])
	for w in without:
		print w
