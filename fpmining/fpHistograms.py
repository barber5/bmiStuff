import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))

from fpCompare import comparePatterns
from mineConcepts import getFromFile

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid, term, concept, grp, cid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def minePatients(goodPairs, candidates):	
	pairDeltas = {}
	invIdx = {}
	patIdxs = {}
	concIdx = {}
	for pid, pat in candidates.iteritems():
		patIdx = {}
		for n in pat['notes']:
			for t in n['terms']:
				print t['grp']
				if str(t['cid']) not in patIdx:
					patIdx[str(t['cid'])] = set([])
				patIdx[str(t['cid'])].add(n['timeoffset'])
				if str(t['cid']) not in invIdx:
					invIdx[str(t['cid'])] = set([])
				invIdx[str(t['cid'])].add(pid)
				if str(t['cid']) not in concIdx:
					concIdx[str(t['cid'])] = t['concept']
		patIdxs[pid] = patIdx	

	for pr, cs in goodPairs.iteritems():		
		t1 = str(pr[0][0])
		t2 = str(pr[1][0])		
		if t1 not in invIdx:			
			continue 		
		pairDeltas[pr] = []		

		for pat in invIdx[t1]:
			patIdx = patIdxs[pat]
			if t1 not in patIdx or t2 not in patIdx:
				continue
			p1 = patIdx[t1]
			p2 = patIdx[t2]
			l1 = list(p1)
			l1 = sorted(l1)
			s1 = l1[0]
			l2 = list(p2)
			l2 = sorted(l2)
			s2 = l2[0]
			delta = s2 - s1
			pairDeltas[pr].append(delta)
		if len(pairDeltas[pr]) == 0:
			del pairDeltas[pr]
		else:
			pd = sorted(pairDeltas[pr])
			pairDeltas[pr] = pd
			print t1+'\t'+t2+'\t'+str(cs['enrichment'])+'\t'+str(cs['freq'])+'\t'+str(cs['other'])+'\t'+str(pd)+'\t'+str(concIdx[t1]+' + '+concIdx[t2])
	return pairDeltas






if __name__ == "__main__":
	print >> sys.stderr, 'usage: <casePairsFile> <controlPairsFile> <casePatientFile> <numberToSample>'
	good = comparePatterns(sys.argv[1], sys.argv[2])
	concs = getFromFile(int(sys.argv[4]), sys.argv[3])

	minePatients(good, concs)