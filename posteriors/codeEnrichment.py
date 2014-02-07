import sys,os, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))

from readIcd9Patients import getInput, binConditionsByAge, selectByAge, binnedTransform, binnedWithCodes, loadCodes
from cohortStats import conditionFrequencies

def getData(codeFile, patientFile, randomFile, minAge, maxAge, freqThreshold):
	codes = loadCodes(codeFile)
	patients = getInput(patientFile)
	randoms = getInput(randomFile)

	binnedPat = binConditionsByAge(patients)	
	selectedPat = selectByAge(binnedPat, minAge, maxAge)	
	xformedPat = binnedTransform(selectedPat, collapse=False, populationFreqThreshold=freqThreshold)
	codedPat = binnedWithCodes(xformedPat, codes)

	binnedRnd = binConditionsByAge(randoms)
	selectedRnd = selectByAge(binnedRnd, minAge, maxAge)
	xformedRnd = binnedTransform(selectedRnd, collapse=False)
	codedRnd = binnedWithCodes(xformedRnd, codes)

	return {
		'patients': codedPat,
		'patientCount': len(codedPat),
		'random': codedRnd,
		'randomCount': len(codedRnd)
	}		

def printEnrichments(patientCount, randomCount):
	for code in (set(patientCount.keys()) | set(randomCount.keys())):
		pat = 0.0
		rnd = 0.0
		codeDesc = ''
		if code in patientCount:
			pat = patientCount[code]['frequency']
			codeDesc = patientCount[code]['desc']
		if code in randomCount:
			rnd = randomCount[code]['frequency']
			codeDesc = randomCount[code]['desc']
		if rnd < .001 and pat < .01:
			continue
		if rnd == 0 and pat > .05: # didn't appear in the random data at all but in more than 5% of condition patients
			incr = float('inf')
		elif rnd == 0:
			continue		
		else:
			incr = 100*float(pat-rnd)/rnd
		if pat == 0 and rnd > .005:
			incr = float('-inf')
		elif pat == 0:
			continue

		print '{}\t{}\t{}\t{}\t{}'.format(code, incr, pat, rnd, codeDesc[:100]+'...')

if __name__ == "__main__":	
	if len(sys.argv) != 9:
		print >> sys.stderr, 'usage: python {} {} {} {} {} {} {} {} {}'.format(sys.argv[0], 'icd9codefile', 'conditionVisits', 'randomVisits', 'minAge', 'maxAge', 'patientSampleRate', 'randomSampleRate', 'freqRequired')
		sys.exit(0)
	data = getData(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[8]))			
	patientCount = conditionFrequencies(data['patients'], data['patientCount'], sample=float(sys.argv[6]))		
	randomCount = conditionFrequencies(data['random'], data['randomCount'], sample=float(sys.argv[7]))

		
	printEnrichments(patientCount, randomCount)

