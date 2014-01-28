from autismClusters import getInput, loadCodes, conditionsBinnedYear, condDictsForAges
import sys, pprint



def countCodes(patientConds, collapse=False):
	condPatients = {}
	for patient, conds in patientConds.iteritems():		
		for age, ageConds in conds.iteritems():
			for cond in ageConds:
				if collapse and cond.find('.') != -1:
					cond = cond.split('.')[0]
				if cond not in condPatients:
					condPatients[cond] = set([])
				condPatients[cond].add(patient)
	return condPatients


if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	codes = loadCodes(sys.argv[2])		
	#diagAges = firstDiag(patients)
	
	patientConds = conditionsBinnedYear(patients)
	count = countCodes(patientConds)
	for code,pats in count.iteritems():
		if code in codes:
			codeDesc = unicode(codes[code], errors='ignore')
		else:
			codeDesc = "None"		
		codeDesc.replace(',', '')
		print '{}\t{}\t{}\t{}'.format(code, len(pats), len(patientConds) - len(pats), codeDesc)
