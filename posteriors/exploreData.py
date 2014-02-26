import sys,os, pprint, json
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCode import getPids, r, decomp
from getTermByID import getTerm

def expForCode(code):
	pids = r.hget('codes', str(code))
	if not pids:
		pids = getPids(code)
		r.hset('codes', str(code), json.dumps(pids))	
	else:
		pids = json.loads(pids)
	print 'got pids'
	result = {}
	for i, pid in enumerate(pids):
		if i > 5:
			break
		if r.hexists('pats', pid):
			resp = r.hget('pats', pid)
			#print resp
			result[pid] = decomp(resp)
			print >> sys.stderr, pid
		else:
			print >> sys.stderr, 'dont have '+str(pid)

	return result

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def termFrequencies(patients):
	terms = {}
	for pat,patDict in patients.iteritems():
		patTerms = {}
		for n in patDict['notes']:
			for t in n['terms']:
				term = (t['termid'], t['negated'], t['familyHistory'])
				if term not in patTerms:
					patTerms[term] = 0
				patTerms[term] += 1
		for term,cnt in patTerms.iteritems():
			if term not in terms:
				terms[term] = 0
			terms[term] += 1
	return terms

def printTerms(pats, rnds):	
	for trm,cnt in pats.iteritems():
		if trm not in rnds:
			rndcnt = 0
		else:			
			rndcnt = rnds[trm
		term = getTerm(trm[0])
		print '{} negated: {}, history: {}\t{}\t{}'.format(term, trm[1], trm[2], cnt, rndcnt)	

if __name__ == "__main__":
	pats = expForCode(sys.argv[1])
	rnd = expForCode(sys.argv[2])
	patTerms = termFrequencies(pats)
	rndTerms = termFrequencies(rnd)
	printTerms(patTerms, rndTerms)