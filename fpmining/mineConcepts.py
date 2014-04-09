import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from getPatient import getPatient, getPatsForCode
from freqPatterns import mineDict
from getTermById import getLab


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
		if pids[next] != 1:
			continue
		print >> sys.stderr, 'grabbing pid: '+str(next)
		resp = getPatient(next)
		if not resp:
			continue
		resp['label'] = 1
		result[next] = resp	
	return result

def getRandoms(num):
	li = getPatsForCode('random')
	result = {}
	while len(result) < num:
		next = str(random.choice(li))
		resp = getPatient(next)
		print >> sys.stderr, 'got '+str(next)+' have gotten '+str(len(result))+' so far'
		if not resp:
			continue
		resp['label'] = 0
		result[next] = resp	
	return result

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid, term, concept, grp, cid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def patientToTimelessConcepts(patient):
	result = {}
	featIdx = {}
	for note in patient['notes']:
		for term in note['terms']:
			cid = term['cid']
			concept = term['concept']			
			cidKey = ('cid', cid, term['negated'], term['familyHistory'])
			if cidKey not in result:
				result[cidKey] = 0
				featIdx[cidKey] = term['concept']
			result[cidKey] += 1
	for l in patient['labs']:
		if 'ord_num' not in l or not l['ord_num'] or l['ord_num'] == '':
			continue
		if 'result_flag' not in l or not l['result_flag'] or l['result_flag'] == '':
			val = 'normal'
		else:
			val = l['result_flag']
		labKey = ('lab', l['proc'], l['component'], val)
		if labKey not in result:
			result[labKey] = 0
			featIdx[labKey] = getLab(l['component'])
		result[labKey] += 1
	return result, featIdx


def mineIt(num, patientFile, thrsh):
	#pats = getFromFile(num, patientFile)
	pats = getRandoms(num)
	conceptVects = {}	
	featIdx = {}
	for pid, pat in pats.iteritems():
		(concDict, feats) = patientToTimelessConcepts(pat)		
		for f,desc in feats.iteritems():
			if f not in featIdx:
				featIdx[f] = desc
		conceptVects[pid] = concDict
	freq = mineDict(conceptVects, thrsh)
	printFreq(freq, featIdx)
	return freq

def printFreq(freq, featIdx):
	for k,v in freq.iteritems():				
		if len(k) != 2:
			continue
		if k[0][0] == 'lab' or k[1][0] == 'lab':
			print k
			print featIdx[k[0]]
			print featIdx[k[1]]
		#print str(v)+'\t'+str(k[0])+'\t'+str(k[1])+'\t'+str(conce)

if __name__ == "__main__":
	print >> sys.stderr, 'usage: <number> <patientFile> <threshold>'
	freq = mineIt(int(sys.argv[1]), sys.argv[2], float(sys.argv[3]))
	










