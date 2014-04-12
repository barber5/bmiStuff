import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
sys.path.append(os.path.realpath('../fpmining'))
sys.path.append(os.path.realpath('./fpmining'))

from queryByCui import r, decomp, compIt
from getTermByID import getTerm, getTermCui, getIngredients, getIngredient, getLab, getConcept
from getPatient import getPatient


def getRandoms(num):
	res = r.hget('codes', 'random')
	li = json.loads(decomp(res))
	result = {}
	while len(result) < num:
		next = str(random.choice(li))
		result[next] = 0
	return result

def getFromFile(num, fileName, rndSrc):
	pids = {}
	result = {}
	with open(fileName, 'r') as fi:
		fi.readline()
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split(' ')
			#print lineArr
			#pidNeg = lineArr[2]
			pidPos = lineArr[0]
			#pids[pidNeg] = 0
			pids[pidPos] = 1
	pidKeys = pids.keys()
	while len(result) < num/2:
		next = random.choice(pidKeys)
		if pids[next] != 1:
			continue
		resp = r.hget('pats', str(next))
		if not resp:
			continue
		result[next] = 1
	if rndSrc == 'file':
		while len(result) < num:
			next = random.choice(pidKeys)
			if pids[next] != 0:
				continue
			resp = r.hget('pats', str(next))
			if not resp:
				continue
			result[next] = 0
	else:
		rnds = getRandoms(num/2)
		for rn in rnds:
			result[rn] = 0
	return result

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def getEnrichments(data):
	featIdx = {}
	posCounts = {}
	negCounts = {}	
	for pid, label in data.iteritems():		
		resp = r.hget('pats', pid)
		if resp == None:
			print >> sys.stderr, 'sad story, have to go and fetch '+str(pid)+' manually'
			resp = getPatient(pid)
			print >> sys.stderr, 'got it'
			pstr = compIt(pat)
			r.hset('pats', pid, pstr)
		#print resp		
		dd = decomp(resp)
		nextPerson = {}
		print >> sys.stderr, str(pid)+': '+str(label)
		for n in dd['notes']:
			for term in n['terms']:
				cid = term['cid']
				concept = term['concept']			
				cidKey = ('cid', cid, term['negated'], term['familyHistory'])
				if cidKey not in nextPerson:
					nextPerson[cidKey] = 0
					featIdx[cidKey] = term['concept']
				nextPerson[cidKey] += 1
		for l in dd['labs']:
			if 'ord_num' not in l or not l['ord_num'] or l['ord_num'] == '':
				continue
			if 'result_flag' not in l or not l['result_flag'] or l['result_flag'] == '':
				val = 'normal'
			else:
				val = l['result_flag']
			labKey = ('lab', l['proc'], l['component'], val)
			if labKey not in nextPerson:
				nextPerson[labKey] = 0
				featIdx[labKey] = getLab(l['component'])
			nextPerson[labKey] += 1



		for p in dd['prescriptions']:			
			ings = getIngredients(p['ingr_set_id'])
			for i in ings:				
				ingKey = ('prescription', i)
				if ingKey not in nextPerson:
					nextPerson[ingKey] = 0
					featIdx[ingKey] = getIngredient(i)
				nextPerson[ingKey] += 1
				
		for feat, val in nextPerson.iteritems():
			if feat not in negCounts:
				negCounts[feat] = 1
			if feat not in posCounts:
				posCounts[feat] = 1
			if label == 1:
				posCounts[feat] += 1
			if label == 0:
				negCounts[feat] += 1
	enrichments = {}
	for feat, posCount in posCounts.iteritems():
		negCount = negCounts[feat]
		enr = float(posCount - negCount) / float(negCount)
		enrichments[feat] = enr
	return (enrichments, featIdx, posCounts, negCounts)


def printEnrichments(enrichments, featIdx, posCounts, negCounts, cutoff):
	for feat, enr in enrichments.iteritems():
		pc = posCounts[feat]
		nc = negCounts[feat]
		desc = featIdx[feat]
		if enr > cutoff:
			print str(feat)+'\t'+str(enr)+'\t'+str(pc)+'\t'+str(nc)+'\t'+str(desc)


if __name__ == "__main__":		
	print >> sys.stderr, 'usage: <patientFile> <dataSetSize> <enrichmentThreshold>'		
	rndSrc = 'cache'

	data = getFromFile(int(sys.argv[2]), sys.argv[1], rndSrc)		
	(enrichments, featIdx, posCounts, negCounts) = getEnrichments(data)
	printEnrichments(enrichments, featIdx, posCounts, negCounts, float(sys.argv[3]))
	

	