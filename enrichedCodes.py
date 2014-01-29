from autismCodeCounter import countCodes
from autismClusters import getInput, loadCodes, conditionsBinnedYear, condDictsForAges
import sys, pprint

if __name__ == "__main__":
	patients = getInput(sys.argv[2])
	randoms = getInput(sys.argv[3])
	codes = loadCodes(sys.argv[1])		
	
	
	patientConds = conditionsBinnedYear(patients)
	patientCount = countCodes(patientConds, sample=float(sys.argv[4]))

	randomConds = conditionsBinnedYear(randoms)
	randomCount = countCodes(randomConds, sample=float(sys.argv[5]))
	



	totalPatients = len(patientConds)
	totalRands = len(randomConds)
	print >> sys.stderr, totalPatients
	print >> sys.stderr, totalRands
	

	for code in (set(patientCount.keys()) | set(randomCount.keys())):
		pat = 0
		rnd = 0
		if code in patientCount:
			pat = len(patientCount[code])
		if code in randomCount:
			rnd = len(randomCount[code])	

		pat = float(pat) / (float(sys.argv[4])*totalPatients)
		rnd = float(rnd) / (float(sys.argv[5])*totalRands)
		if code in codes:
			codeDesc = unicode(codes[code], errors='ignore')
		else:
			continue
			codeDesc = "None"		
		codeDesc.replace(',', '')
		if rnd < .01 and pat < .01:
			continue
		if rnd == 0 and pat > .05:
			incr = float('inf')
		elif rnd == 0:
			continue		
		else:
			incr = 100*float(pat-rnd)/rnd
		if pat == 0 and rnd > .05:
			incr = float('-inf')
		elif pat == 0:
			continue
		print '{}\t{}\t{}\t{}\t{}'.format(code, incr, pat, rnd, codeDesc)
