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
from pygraphml.GraphMLParser import *
from pygraphml.Graph import *
from pygraphml.Node import *
from pygraphml.Edge import *



# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def getEdges(enrichments, patients):
	singletons = {}
	pairs = {}
	for pid, dd in patients.iteritems():	
		print >> sys.stderr, 'edging pid: '+str(pid)										
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

		for v in dd['visits']:
			code = v['icd9']
			if code == '':
				continue
			offs = int(round(v['timeoffset']))
			codeArr = code.split(',')
			for code in codeArr:
				codeKey = ('code', code)
				if codeKey in enrichments:
					if codeKey not in singletons:
						singletons[codeKey] = set([])
					singletons[codeKey].add((pid, offs))

	result = {}
	print >> sys.stderr, 'getting pairs from singletons: '+str(len(singletons.keys()))
	for i in range(len(singletons.keys())):
		for j in range(i+1, len(singletons.keys())):
			f1 = singletons.keys()[i]
			f2 = singletons.keys()[j]
			ps1 = set([d[0] for d in singletons[f1]])
			
			ps2 = set([d[0] for d in singletons[f2]])
			
			ps12 = ps1&ps2							
			c1 = float(len(ps1))/float(len(patients.keys()))	
			c2 = float(len(ps2))/float(len(patients.keys()))	
			c12and = float(len(ps12)) / float(len(patients.keys()))			
			if c12and == c1 and c1 < .1:
				continue
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
				f12f = 1
				f21f = 1
				totalOffset = 0.0
				totalPats = 0.0
				for pat, feats in both.iteritems():		
				    # find the first occurence of f1 and f2 for this patient			
					min1 = float('inf')
					min2 = float('inf')
					for o1 in feats[f1]:
						if o1 < min1:
							min1 = o1
						for o2 in feats[f2]:
							if o2 < min2:
								min2 = o2
							if o1 < o2:
								f12 += 1
							elif o1 > o2:
								f21 += 1
					if min1 == float('inf') or min2 == float('inf'):
						continue
					else:
						totalPats += 1
					totalOffset += min2 - min1
					if min1 < min2:
						f12f += 1

					elif min2 < min2:
						f21f += 1
				avgOffset = float(totalOffset)/float(len(both.keys()))
				lam = math.log(float(f12)/float(f21), 2.0)
				lf = math.log(float(f12f)/float(f21f), 2.0)
				if lf < 0:
					first = f2
					second = f1
					count1 = c2
					count2 = c1
					lam = -lam
					lf = -lf
					avgOffset = -avgOffset
				else:
					first = f1
					second = f2
					count1 = c1
					count2 = c2
				result[(first, second)] = {
					'f1': first,
					'f1desc': enrichments[first]['description'],
					'f1enrich': enrichments[first]['enrichment'],
					'f2enrich': enrichments[second]['enrichment'],
					'f1freq': count1,
					'f2': second,
					'f2freq': count2,
					'intersection': c12and,
					'independent': c1*c2,
					'f2desc': enrichments[second]['description'],					
					'lambda': lam,
					'lambdaFirst': lf, 
					'avgOffset': avgOffset,
					'lift': math.log(float(c12and)/float(c1*c2), 2.0)
				}					
	return result




def printEdges(edges, cutoff=.01):
	for pr, meta in edges.iteritems():
		if meta['intersection'] > cutoff:
			print str(meta['f1']) + '\t' + str(meta['f2']) + '\t' + str(meta['lambda']) + '\t' + str(meta['lambdaFirst']) + '\t' + str(meta['lift']) + '\t' + str(meta['independent']) + '\t' + str(meta['f1freq']) + '\t' + str(meta['f2freq']) + '\t' + str(meta['intersection']) + '\t' + str(meta['avgOffset'])+'\t'+str(meta['f1enrich']+'\t'+str(meta['f2enrich'])+'\t'+str(meta['f1desc']) + '\t'+str(meta['f2desc'])
	print >> sys.stderr, '<f1> <f2> <lambda> <lambdaFirst> <lift> <f1freq*f2freq> <f1freq> <f2freq> <intersection> <f1desc+f2desc>'

if __name__ == "__main__":
	print >> sys.stderr, 'usage: <enrichmentsFile> <patientFile> <numPatients>'
	enr = getEnrichments(sys.argv[1])
	pats = getPatients(int(sys.argv[3]), sys.argv[2])
	print >> sys.stderr, 'getting edges'
	edges = getEdges(enr, pats)
	print >> sys.stderr, 'got edges'
	printEdges(edges)
	
