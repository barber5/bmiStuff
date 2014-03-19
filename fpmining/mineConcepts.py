import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from getPatient import getPatient, getPatsForCode



def getFromFile(num, fileName):
	pids = {}
	result = {}
	with open(fileName, 'r') as fi:
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split(' ')
			#print lineArr
			if len(lineArr) > 2:
				pidNeg = lineArr[2]
				pids[pidNeg] = 0
			pidPos = lineArr[1]			
			pids[pidPos] = 1
	pidKeys = pids.keys()
	while len(result) < num:
		next = random.choice(pidKeys)
		print 'grabbing pid: '+str(next)
		if pids[next] != 1:
			continue
		resp = getPatient(next)
		if not resp:
			continue
		result[next] = 1	
	return result

def getRandoms(num):
	li = getPatsForCode('random')
	result = {}
	while len(result) < num:
		next = str(random.choice(li))
		result[next] = 0
	return result

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid, term, concept, grp, cid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def patientToTimelessConcepts(patient, conceptIdx):
	result = {}
	for note in patient['notes']:
		for term in note['terms']:
			cid = term['cid']
			concept = term['concept']
			if cid not in conceptIdx:
				conceptIdx[cid] = concept
			cidKey = (cid, term['negated'], term['familyHistory'])
			if cidKey not in result:
				result[cidKey] = 0
			result[cidKey] += 1
	return result


def mineIt(num, patientFile):
	pats = getFromFile(num, patientFile)
	conceptVects = []
	conceptIdx = {}
	for pat in pats:
		conceptVects.append(patientToTimelessConcepts(pat), conceptIdx)
	return conceptVects

if __name__ == "__main__":
	pprint.pprint(mineIt(int(sys.argv[1]), sys.argv[2]))










