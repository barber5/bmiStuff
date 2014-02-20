from codeEnrichment import getData
import sys,os, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))

from readIcd9Patients import getInput, binConditionsByAge, selectByAge, binnedTransform, binnedWithCodes, loadCodes
from cohortStats import conditionFrequencies

def printRRs(patientCount, randomCount):
	pprint.pprint(patientCount)
	#pprint.pprint(randomCount)

if __name__ == "__main__":	
	if len(sys.argv) != 9:
		print >> sys.stderr, 'usage: python {} {} {} {} {} {} {} {} {}'.format(sys.argv[0], 'icd9codefile', 'conditionVisits', 'randomVisits', 'minAge', 'maxAge', 'patientSampleRate', 'randomSampleRate', 'freqRequired')
		sys.exit(0)

	data = getData(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[8]))			
	patientCount = conditionFrequencies(data['patients'], data['patientCount'], sample=float(sys.argv[6]))		
	randomCount = conditionFrequencies(data['random'], data['randomCount'], sample=float(sys.argv[7]))

		
	printRRs(patientCount, randomCount)