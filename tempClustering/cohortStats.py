import sys, pprint, random
from readIcd9Patients import getInput, loadCodes, binConditionsByAge, selectByAge, binnedTransform, binnedWithCodes

# input: {pid -> [{cond -> {count, desc}}]}
# output: {cond -> freq}
def conditionFrequencies(patients, sampleSize, sample=None):
	result = {}	
	if sample:
		sampleSize = sample*sampleSize
	for pid, conds in patients.iteritems():		
		rnd = random.random()
		#	print rnd, sample
		if sample and rnd > sample:
			continue		
		for cond, cc in conds.iteritems():							
			if cond not in result:
				result[cond] = {
					'frequency': 0.0,
					'desc': cc['desc']
				}			
			result[cond]['frequency'] += 1.0/float(sampleSize)		
	return result

def printFreqs(freqs):
	for cond, fd in freqs.iteritems():
		print '{}\t{}\t{}'.format(cond, fd['frequency'], fd['desc'][:100]+'...')
	
if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])
	binned = binConditionsByAge(patients)
	selected = selectByAge(binned, int(sys.argv[3]), int(sys.argv[4]))
	xformed = binnedTransform(selected, collapse=False, populationFreqThreshold=.02)
	coded = binnedWithCodes(xformed, codes)
	freqs = conditionFrequencies(coded, len(patients), sample=float(sys.argv[5]))
	printFreqs(freqs)