import sys,os, pprint, json, random, pprint
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


def getCounts(enrichments, patients):	
	singletons = {}
	pairs = {}
	for pid, dd in patients.iteritems():											
		for n in dd['notes']:			
			for term in n['terms']:
				cid = term['cid']
				concept = term['concept']			
				cidKey = ('cid', cid, term['negated'], term['familyHistory'])				
				if cidKey in enrichments:
					if cidKey not in singletons:
						singletons[cidKey] = set([])
					singletons[cidKey].add(pid)				
		for l in dd['labs']:
			if 'ord_num' not in l or not l['ord_num'] or l['ord_num'] == '':
				continue
			if 'result_flag' not in l or not l['result_flag'] or l['result_flag'] == '':
				val = 'normal'
			else:
				val = l['result_flag']
			
			labKey = ('lab', l['proc'], l['component'], val)			
			if labKey in enrichments:
				if labKey not in singletons:
					singletons[labKey] = set([])
				singletons[labKey].add(pid)

		for p in dd['prescriptions']:				
			ings = getIngredients(p['ingr_set_id'])
			for i in ings:				
				ingKey = ('prescription', i)	
				if ingKey in enrichments:			
					if ingKey not in singletons:
						singletons[ingKey] = set([])
					singletons[ingKey].add(pid)
		
	for i in range(len(singletons.keys())):
		for j in range(i+1, len(singletons.keys())):
			f1 = singletons.keys()[i]
			f2 = singletons.keys()[j]
			ps1 = singletons[f1]
			ps2 = singletons[f2]
			c1 = float(len(ps1))/float(len(patients.keys()))
			c2 = len(ps2)/float(len(patients.keys()))
			c12and = len(ps1&ps2)/float(len(patients.keys()))
			c12or = len(ps1|ps2)/float(len(patients.keys()))
			c1only = c12and - c2
			c2only = c12and - c1
			if f1 < f2:
				pr = (f1, f2)
			else:
				pr = (f2, f1)
			pairs[pr] = {
				'f1': pr[0],
				'f1desc': enrichments[pr[0]]['description'],
				'f2': pr[1],
				'f2desc': enrichments[pr[1]]['description'],
				'count1': c1,
				'count2': c2,
				'intersection': c12and,
				'union': c12or,
				'count1unique': c1only,
				'count2unique': c2only,
				'lift': float(c12and)/float(c1*c2)
			}
	return pairs
	
	
def printPairs(prs):
	for pr, data in prs.iteritems():
		if data['intersection'] > .1 and data['lift'] > .5:
			print str(pr)+'\t'+str(data['lift'])+'\t'+str(data['intersection'])+'\t'+str(data['f1desc']+' + '+data['f2desc'])

if __name__ == "__main__":
	print >> sys.stderr, 'usage: <enrichmentsFile> <patientFile> <numPatients>'
	enr = getEnrichments(sys.argv[1])
	pats = getPatients(int(sys.argv[3]), sys.argv[2])
	prs = getCounts(enr, pats)
	printPairs(prs)