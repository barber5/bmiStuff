import sys,os, pprint, json, random, pprint, math
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))

from fpCompare import comparePatterns
from mineConcepts import getFromFile

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid, term, concept, grp, cid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }


# a different idea is to instead of looking at the first time a term appears, we could look at every appearance of a candidate term 

# so is there entropy in the offsets here or not??
def minePatients(goodPairs, candidates):	
	pairDeltas = {}
	invIdx = {}
	patIdxs = {}
	concIdx = {}
	for pid, pat in candidates.iteritems():
		patIdx = {}
		for n in pat['notes']:
			for t in n['terms']:
				#print t['grp']
				if str(t['cid']) not in patIdx:
					patIdx[str(t['cid'])] = set([])
				patIdx[str(t['cid'])].add(n['timeoffset'])
				if str(t['cid']) not in invIdx:
					invIdx[str(t['cid'])] = set([])
				invIdx[str(t['cid'])].add(pid)
				if str(t['cid']) not in concIdx:
					concIdx[str(t['cid'])] = t['concept']
		patIdxs[pid] = patIdx	
	maxDelta = 0
	minDelta = 0
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
			if delta > maxDelta:
				maxDelta = delta
			if delta < minDelta:
				minDelta = delta
			pairDeltas[pr].append(delta)
		if len(pairDeltas[pr]) == 0:
			del pairDeltas[pr]
		else:
			pds = sorted(pairDeltas[pr])
			pairDeltas[pr] = pds
			total = 0.0
			for pd in pds:
				total += pd
			avg = float(total)/float(len(pds))
			totalDev = 0.0			
			for pd in pds:
				totalDev += (pd - avg)*(pd-avg)
			stdDevSq = float(totalDev)/float(len(pds) - 1.0)
			stdDev = math.sqrt(stdDevSq)

			print t1+'\t'+t2+'\t'+str(cs['enrichment'])+'\t'+str(cs['freq'])+'\t'+str(cs['other'])+'\t'+str(avg)+'\t'+str(stdDev)+'\t'+str(pd)+'\t'+str(concIdx[t1]+' + '+concIdx[t2])
	




def getPairBins(minDelta, maxDelta, pairDeltas):
	bins = []
	for i in range(int(math.floor(minDelta)), int(math.ceil(maxDelta))+100, 100):
		bins.append((i, i+100))
	pairBins = {}	
	for pr, deltas in pairDeltas.iteritems():
		pairBins[pr] = {}
		deltIdx = 0
		for b in bins:
			low = b[0]
			hi = b[1]
			count = 0
			while deltIdx < len(deltas):
				nextDelt = deltas[deltIdx]
				if nextDelt > hi:
					break
				count += 1
				deltIdx += 1
			pairBins[pr][b] = count
	firstLinePrinted = False
	firstLine = ''
	secondLine = ''
	i = 1
	for pr, feats in pairBins.iteritems():
		for bin, count in feats.iteritems():
			if not firstLinePrinted:				
				if len(firstLine) == 0:
					firstLine = str(bin)
					secondLine = str(count)
				else:
					firstLine += '\t'+str(bin)
					secondLine += '\t'+str(count)
			else: 
				if len(secondLine) == 0:
					secondLine = str(count)
				else:
					secondLine += '\t'+str(count)

		if not firstLinePrinted:
			print firstLine			
			firstLinePrinted = True
		print secondLine
		secondLine = ''

	return pairBins

if __name__ == "__main__":
	print >> sys.stderr, 'usage: <casePairsFile> <controlPairsFile> <casePatientFile> <numberToSample>'
	good = comparePatterns(sys.argv[1], sys.argv[2])
	concs = getFromFile(int(sys.argv[4]), sys.argv[3])

	minePatients(good, concs)




