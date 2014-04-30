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
				for pat, feats in both.iteritems():
					min1 = float('inf')
					min2 = float('inf')
					for o1 in feats[f1]:
						if o1 < min1:
							min1 = o1
						for o2 in feats[f2]:
							if o2 < min2:
								min2 = 01
							if o1 < o2:
								f12 += 1
							elif o1 > o2:
								f21 += 1
					if min1 < min2:
						f12f += 1
					elif min2 < min2:
						f21f += 1
				lam = math.log(float(f12)/float(f21))
				lf = math.log(float(f12f)/float(f21f))
				if lam < 0:
					first = f2
					second = f1
					count1 = c2
					count2 = c1
					lam = -lam
					lf = -lf
				else:
					first = f1
					second = f2
					count1 = c1
					count2 = c2
				result[(f1, f2)] = {
					'f1': f1,
					'f1desc': enrichments[f1]['description'],
					'f1freq': count1,
					'f2': f2,
					'f2freq': count2,
					'intersection': c12and,
					'independent': c1*c2,
					'f2desc': enrichments[f2]['description'],					
					'lambda': lam,
					'lambdaFirst': lf, 
					'lift': math.log(float(c12and)/float(c1*c2))
				}					
	return result

def analyzeEdges(edges):
	graph = {}
	for pr, meta in edges.iteritems():
		f1 = meta['f1']
		f1 = (f1, meta['f1desc'])
		if meta['f1freq'] < .1:
			continue
		if f1 not in graph:
			graph[f1] = {
				'in': {},
				'out': {},
				'adjacent': {},
				'desc': meta['f1desc'],
				'freq': meta['f1freq']
			}
		f2 = meta['f2']
		f2 = (f2, meta['f2desc'])
		if meta['f2freq'] < .1:
			continue

		if f2 not in graph:
			graph[f2] = {
				'in': {},
				'out': {},
				'adjacent': {},
				'desc': meta['f2desc'],
				'freq': meta['f2freq']
			}
		if meta['lambda'] > .5:
			graph[f1]['out'][f2] = {
				'lambda': meta['lambda']
			}
			graph[f2]['in'][f1] = {
				'lambda': meta['lambda']
			}
		else:

			if meta['lift'] > 2:
				graph[f1]['adjacent'][f2] = {
					'lift': meta['lift']
				}
				graph[f2]['adjacent'][f1] = {
					'lift': meta['lift']
				}
			None
	return graph

def inOutGraph(graphDict):
	g = Graph()
	nDict = {}
	for node, meta in graphDict.iteritems():
		if len(meta['out']) == 0 and len(meta['in']) == 0:
			continue
		n = g.add_node(node)			
		n['freq'] = meta['freq']
		nDict[node] = n
	for node, meta in graphDict.iteritems():
		if node not in nDict:
			continue
		n = nDict[node]			
		for node2 in meta['in']:
			n2 = nDict[node2]
			g.add_edge(n2, n, directed=True)
	parser = GraphMLParser()
	parser.write(g, "inout.graphml")

def adjacenciesGraph(graphDict):
	g = Graph()
	nDict = {}
	for node, meta in graphDict.iteritems():
		n = g.add_node(node)			
		n['freq'] = meta['freq']
		nDict[node] = n
	for node, meta in graphDict.iteritems():
		n = nDict[node]			
		for node2 in meta['adjacent']:
			n2 = nDict[node2]
			g.add_edge(n2, n, directed=True)
	parser = GraphMLParser()
	parser.write(g, "adj.graphml")

def printEdges(edges, cutoff=.05):
	for pr, meta in edges.iteritems():
		if meta['intersection'] > cutoff:
			print str(meta['f1']) + '\t' + str(meta['f2']) + '\t' + str(meta['lambda']) + '\t' + str(meta['lambdaFirst']) + '\t' + str(meta['lift']) + '\t' + str(meta['independent']) + '\t' + str(meta['f1freq']) + '\t' + str(meta['f2freq']) + '\t' + str(meta['intersection']) + '\t' + str(meta['f1desc']) + ' + '+str(meta['f2desc'])
	print >> sys.stderr, '<f1> <f2> <lambda> <lambdaFirst> <lift> <f1freq*f2freq> <f1freq> <f2freq> <intersection> <f1desc+f2desc>'

if __name__ == "__main__":
	print >> sys.stderr, 'usage: <enrichmentsFile> <patientFile> <numPatients> <intersectionCutoff>'
	enr = getEnrichments(sys.argv[1])
	pats = getPatients(int(sys.argv[3]), sys.argv[2])
	edges = getEdges(enr, pats)
	#printEdges(edges, float(sys.argv[4]))
	graph = analyzeEdges(edges)
	inOutGraph(graph)
