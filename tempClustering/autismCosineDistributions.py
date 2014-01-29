from autismClusters import getInput, loadCodes, conditionsBinnedYear, condDictsForAges
import sys, pprint
from sklearn.feature_extraction import DictVectorizer
from scipy.spatial.distance import cosine


def getCosineDistribution(patientConds, minAge, maxAge):
	conditionDictionaries = condDictsForAges(patientConds, range(minAge, maxAge+1))		
	measurements = []
	for patient, conds in conditionDictionaries.iteritems():
		measurements.append(conds)
	vec = DictVectorizer()
	featArray = vec.fit_transform(measurements).toarray()
	dists = []
	for i in range(len(featArray)):
		for j in range(i+1, len(featArray)):
			dist = cosine(featArray[i], featArray[j])
			if dist > .999:
				continue
			dists.append(str(dist))
	return dists


if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])		
	patientConds = conditionsBinnedYear(patients)
	dists = getCosineDistribution(patientConds, int(sys.argv[3]), int(sys.argv[4]))
	print ','.join(dists)