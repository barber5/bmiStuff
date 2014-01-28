from autismCodeCounter import countCodes
from autismClusters import getInput, loadCodes, conditionsBinnedYear, condDictsForAges
import sys, pprint

if __name__ == "__main__":
	patients = getInput(sys.argv[2])
	randoms = getInput(sys.argv[3])
	codes = loadCodes(sys.argv[1])		
	
	
	patientConds = conditionsBinnedYear(patients)
	patientCount = countCodes(patientConds)

	randomConds = conditionsBinnedYear(randoms)
	randomCount = countCodes(randomConds)

	for code in (set(patientCount.keys()) | set(randomCount.keys())):
		pat = 0
		rnd = 0
		if code in patientCount:
			pat = len(patientCount[code])
		if code in randomCount:
			rnd = len(randomCount[code])
		if code in codes:
			codeDesc = unicode(codes[code], errors='ignore')
		else:
			codeDesc = "None"		
		codeDesc.replace(',', '')
		if rnd == 0:
			incr = 10000000000+pat
		else:
			incr = 100*float(pat-rnd)/rnd
		print '{}\t{}\t{}'.format(code, incr, codeDesc)
