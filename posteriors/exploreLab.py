import sys,os, pprint, json, random
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCode import getPids, r, decomp, compIt
from getTermByID import getTerm, getTermCui

def expForCode(code, sampleRate):
	pids = r.hget('codes', str(code))
	if not pids:
		pids = getPids(code)
		r.hset('codes', str(code), compIt(json.dumps(pids)))
	else:
		pids = decomp(pids)
		try:
			pids = json.loads(pids)
		except Exception as e:
			print >> sys.stderr, 'was not json'
	print >> sys.stderr, 'got %s pids' % str(len(pids))
	result = {}
	for i, pid in enumerate(pids):
		if random.random() > sampleRate:
			continue
		if r.hexists('pats', pid):
			resp = r.hget('pats', pid)
			#print resp
			dd = decomp(resp)
			result[pid] = {'labs': dd['labs']}			
			print >> sys.stderr, str(i)+' '+str(pid)
		else:
			print >> sys.stderr, 'dont have '+str(pid)
	return result

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def labFrequencies(patients, freqThreshold=0.0):
	terms = {}
	for pat,patDict in patients.iteritems():
		patTerms = {}
		for n in patDict['labs']:		
			if 'result_flag' not in n or not n['result_flag'] or n['result_flag'] == '':
				continue
			term = (n['description'], n['component'], n['result_flag'])
			if term not in patTerms:
				patTerms[term] = 0
			patTerms[term] += 1
		for term,cnt in patTerms.iteritems():			
			if term not in terms:
				terms[term] = 0
			terms[term] += 1
	print >> sys.stderr, "Got "+str(len(terms.keys())) +" labs"
	newResult = {}
	for trm, cnt in terms.iteritems():
		if float(cnt)/ len(patients.keys()) < freqThreshold:
			continue
		else:
			newResult[trm] = float(cnt)/ len(patients.keys())
	return newResult

def printTerms(pats, rnds):	
	for trm,cnt in pats.iteritems():
		if trm not in rnds:
			rndcnt = 0
			continue
		else:			
			rndcnt = rnds[trm]
		#print >> sys.stderr, trm
		term = trm[0]
		#print term
		if rndcnt == 0:
			increase = 9999
		else:
			increase = float(cnt - rndcnt)/float(rndcnt)
		print '%s negated: %s history: %s\t%s\t%s\t%s' % (term, str(trm[1]), str(trm[2]), str(cnt), str(rndcnt), str(increase))
	'''
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
		print '%s negated: %s history: %s\t%s\t%s\t%s' % (term, str(trm[1]), str(trm[2]), str(patcnt), str(cnt), str(increase))'''

if __name__ == "__main__":
	if len(sys.argv) != 7:
		print >> sys.stderr, 'usage: python %s %s %s %s %s %s %s' % (sys.argv[0], '<code1>', '<code2>', '<code1FreqCutoff>', '<code2FreqCutoff>', '<code1SampleRate>', '<code2SampleRate>')
		sys.exit(1)
	pats = expForCode(sys.argv[1], float(sys.argv[5]))
	rnd = expForCode(sys.argv[2], float(sys.argv[6]))
	patTerms = labFrequencies(pats, float(sys.argv[3]))
	rndTerms = labFrequencies(rnd, float(sys.argv[4]))
	#pprint.pprint(rndTerms)
	printTerms(patTerms, rndTerms)




