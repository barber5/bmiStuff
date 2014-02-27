import sys,os, pprint, json
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCode import getPids, r, decomp, compIt
from getTermByID import getTerm

def expForCode(code):
	pids = r.hget('codes', str(code))
	if not pids:
		pids = getPids(code)
		r.hset('codes', str(code), compIt(json.dumps(pids)))
	else:
		pids = decomp(pids)
		pids = json.loads(pids)
	print >> sys.stderr, 'got pids'
	result = {}
	for i, pid in enumerate(pids):
		if i > 20:
			break
		if r.hexists('pats', pid):
			resp = r.hget('pats', pid)
			#print resp
			result[pid] = decomp(resp)
			print >> sys.stderr, str(i)+' '+str(pid)
		else:
			print >> sys.stderr, 'dont have '+str(pid)

	return result

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def termFrequencies(patients, freqThreshold=0.0):
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
	newResult = {}
	for trm, cnt in terms.iteritems():
		if float(cnt)/ len(patients.keys()) < freqThreshold:
			continue
		else:
			newResult[trm] = cnt
	return newResult

def printTerms(pats, rnds):	
	for trm,cnt in pats.iteritems():
		if trm not in rnds:
			rndcnt = 0
			continue
		else:			
			rndcnt = rnds[trm]
		#print >> sys.stderr, trm
		term = getTerm(trm[0])
		#print term
		if rndcnt == 0:
			increase = 9999
		else:
			increase = float(cnt - rndcnt)/float(rndcnt)
		print '%s negated: %s history: %s\t%s\t%s\t%s' % (term, str(trm[1]), str(trm[2]), str(cnt), str(rndcnt), str(increase))
	for trm, cnt, in rnds.iteritems():
		#print trm
		if trm not in pats:
			patcnt = 0
			continue
		else:
			patcnt = pats[trm]
		term = getTerm(trm[0])
		if patcnt == 0:
			increase = -9999
		else:
			increase = float(cnt - rndcnt)/float(patcnt)
		print '%s negated: %s history: %s\t%s\t%s\t%s' % (term, str(trm[1]), str(trm[2]), str(patcnt), str(cnt), str(increase))

if __name__ == "__main__":
	pats = expForCode(sys.argv[1])
	rnd = expForCode(sys.argv[2])
	patTerms = termFrequencies(pats, float(sys.argv[3]))
	rndTerms = termFrequencies(rnd, float(sys.argv[4]))
	#pprint.pprint(rndTerms)
	printTerms(patTerms, rndTerms)




