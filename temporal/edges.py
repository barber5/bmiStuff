import sys,os, pprint, json, random, pprint, math
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
sys.path.append(os.path.realpath('../fpmining'))
sys.path.append(os.path.realpath('./fpmining'))

from queryByCui import r, decomp, compIt
from getTermByID import getTerm, getTermCui, getIngredients, getIngredient, getLab, getConcept
from ast import literal_eval as make_tuple
from mineConcepts import getFromFile
from beforeAfter import getEnrichments, getPatients


# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def getEdges(enrichments, patients):
	singletons = {}
	pairs = {}
	for pid, dd in patients.iteritems():											
		for n in dd['notes']:			
			for term in n['terms']:
				offs = int(round(n['timeoffset']))
				cid = term['cid']
				concept = term['concept']			
				cidKey = ('cid', cid, term['negated'], term['familyHistory'])				
				if cidKey in enrichments:
					if cidKey not in singletons:
						singletons[cidKey] = set([])
					singletons[cidKey].add((pid, offs))
		for l in dd['labs']:
			if 'ord_num' not in l or not l['ord_num'] or l['ord_num'] == '':
				continue
			if 'result_flag' not in l or not l['result_flag'] or l['result_flag'] == '':
				val = 'normal'
			else:
				val = l['result_flag']
			offs = int(round(l['timeoffset']))
			labKey = ('lab', l['proc'], l['component'], val)			
			if labKey in enrichments:
				if labKey not in singletons:
					singletons[labKey] = set([])
				singletons[labKey].add((pid, offs))

		for p in dd['prescriptions']:	
			offs = int(round(p['timeoffset']))		
			ings = getIngredients(p['ingr_set_id'])
			for i in ings:				
				ingKey = ('prescription', i)	
				if ingKey in enrichments:			
					if ingKey not in singletons:
						singletons[ingKey] = set([])
					singletons[ingKey].add((pid, offs))

	result = {}
		
	for i in range(len(singletons.keys())):
		for j in range(i+1, len(singletons.keys())):
			f1 = singletons.keys()[i]
			f2 = singletons.keys()[j]
			ps1 = set([d[0] for d in singletons[f1]])
			ps2 = set([d[0] for d in singletons[f2]])
			ps12 = ps1&ps2		
			c1 = float(len(ps1))/float(len(pats.keys()))	
			c2 = float(len(ps2))/float(len(pats.keys()))	
			c12and = len(ps12)
			both = {}
			if c12and > 0:
				for pr in singletons[f1]:
					pat = pr[0]
					if pat in ps12:
						if pat not in both:
							both[pat] = {
								f1: [],
								f2: []
							}
						offs = pr[1]
						both[pat][f1].append(offs)
				for pr in singletons[f2]:
					pat = pr[0]
					if pat in ps12:
						if pat not in both:
							both[pat] = {
								f1: [],
								f2: []
							}
						offs = pr[1]
						both[pat][f2].append(offs)
				f12 = 1
				f21 = 1
				for pat, feats in both.iteritems():
					for o1 in feats[f1]:
						for o2 in feats[f2]:
							if o1 < o2:
								f12 += 1
							elif o1 > o2:
								f21 += 1
				result[(f1, f2)] = {
					'f1': f1,
					'f1desc': enrichments[f1]['description'],
					'f1freq': c1,
					'f2': f2,
					'f2freq': c2,
					'intersection': c12and,
					'f2desc': enrichments[f2]['description'],					
					'lambda': math.log(float(f12)/float(f21))
				}					
	return result

def printEdges(edges):
	for pr, meta in edges.iteritems():
		print str(meta['f1'])+': '+str(meta['f1desc']) + '\t' + str(meta['f2'])+': '+str(meta['f2desc']) + '\t' + str(meta['lambda']) + '\t' + str(meta['f1freq']) + '\t' + str(meta['f2freq']) + '\t' + str(meta['intersection'])

if __name__ == "__main__":
	print >> sys.stderr, 'usage: <enrichmentsFile> <patientFile> <numPatients>'
	enr = getEnrichments(sys.argv[1])
	pats = getPatients(int(sys.argv[3]), sys.argv[2])
	edges = getEdges(enr, pats)
	printEdges(edges)
