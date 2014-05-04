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


def inOutGraph(graphDict, gFile):
	g = Graph()
	nDict = {}
	for node, meta in graphDict.iteritems():		
		n = g.add_node(node[0][0]+': '+node[1])			
		n['freq'] = meta['freq']
		n['type'] = node[0][0]
		n['enrichment'] = meta['enrichment']		
		nDict[node] = n
	for node, meta in graphDict.iteritems():
		if node not in nDict:
			continue
		n = nDict[node]			
		for node2, edgeMeta in meta['in'].iteritems():			
			n2 = nDict[node2]
			e = g.add_edge(n2, n, directed=True)
			e['lift'] = edgeMeta['lift']
			e['lambda'] = edgeMeta['lambda']
			e['lambdaFirst'] = edgeMeta['lambdaFirst']		
			e['avgOffset'] = edgeMeta['avgOffset']	
			e['intersection'] = edgeMeta['intersection']
	parser = GraphMLParser()
	parser.write(g, 'tmp/'+gFile)
	with open(gFile, 'w') as fi
		with open('tmp/'+gFile, 'r') as fi2:
			while True:
				line = fi2.readline()
				if line == '':
					break
				if line.find('attr.name="freq"') != -1:
					fi.write('    <key attr.name="freq" attr.type="double" id="freq"/>\n')
				elif line.find('attr.name="enrichment"') != -1:
					fi.write('    <key attr.name="enrichment" attr.type="double" id="enrichment"/>\n')
				elif line.find('attr.name="avgOffset"') != -1:
					fi.write('    <key attr.name="avgOffset" attr.type="double" id="avgOffset"/>\n')
				elif line.find('attr.name="intersection"') != -1:
					fi.write('    <key attr.name="intersection" attr.type="double" id="intersection"/>\n')
				elif line.find('attr.name="lift"') != -1:
					fi.write('    <key attr.name="lift" attr.type="double" id="lift"/>\n')
				elif line.find('attr.name="lambdaFirst"') != -1:
					fi.write('    <key attr.name="lambdaFirst" attr.type="double" id="lambdaFirst"/>\n')
				elif line.find('attr.name="lambda"') != -1:
					fi.write('    <key attr.name="lambda" attr.type="double" id="lambda"/>\n')
				else:
					fi.write(line)



def analyzeEdges(edges, intersectionCutoff=.05, cutoff=.01, lift=1.0):
	graph = {}
	for pr, meta in edges.iteritems():
		f1 = meta['f1']
		f1 = (f1, meta['f1desc'])
		if meta['f1freq'] < cutoff:
			continue
		
		f2 = meta['f2']
		f2 = (f2, meta['f2desc'])
		if meta['f2freq'] < cutoff:
			continue
		if f1 not in graph:
			graph[f1] = {
				'in': {},
				'out': {},
				'adjacent': {},
				'desc': meta['f1desc'],
				'freq': meta['f1freq'],
				'enrichment': meta['f1enrich']
			}
		if f2 not in graph:
			graph[f2] = {
				'in': {},
				'out': {},
				'adjacent': {},
				'desc': meta['f2desc'],
				'freq': meta['f2freq'],
				'enrichment': meta['f2enrich']
			}
		
		if meta['lift'] > lift and meta['intersection'] > intersectionCutoff:
			if meta['lambdaFirst'] > 0:
				graph[f1]['out'][f2] = {
					'lambda': meta['lambda'],
					'lambdaFirst': meta['lambdaFirst'],
					'lift': meta['lift'],
					'avgOffset': meta['avgOffset'],
					'intersection': meta['intersection']
				}
				graph[f2]['in'][f1] = {
					'lambda': meta['lambda'],
					'lambdaFirst': meta['lambdaFirst'],
					'lift': meta['lift'],
					'avgOffset': meta['avgOffset'],
					'intersection': meta['intersection']
				}
			else:
				graph[f2]['out'][f1] = {
					'lambda': -meta['lambda'],
					'lambdaFirst': -meta['lambdaFirst'],
					'lift': meta['lift'],
					'avgOffset': -meta['avgOffset'],
					'intersection': meta['intersection']					
				}
				graph[f1]['in'][f2] = {
					'lambda': -meta['lambda'],
					'lambdaFirst': -meta['lambdaFirst'],
					'lift': meta['lift'],
					'avgOffset': -meta['avgOffset'],
					'intersection': meta['intersection']
				}
		
	return graph


def edgesFromFile(edgeFile):
	edges = {}
	with open(edgeFile, 'r') as fi:
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			
			lineArr = line.split('\t')
			tp1 = make_tuple(lineArr[0])
			tp2 = make_tuple(lineArr[1])
			pr = (tp1, tp2)
			edges[pr] = {
				'f1': tp1,
				'f2': tp2,
				'lambda': float(lineArr[2]),
				'lambdaFirst': float(lineArr[3]),
				'lift': float(lineArr[4]),
				'independent': float(lineArr[5]),
				'f1freq': float(lineArr[6]),
				'f2freq': float(lineArr[7]),
				'intersection': float(lineArr[8]),
				'avgOffset': float(lineArr[9]),
				'f1enrich': float(lineArr[10]),
				'f2enrich': float(lineArr[11]),
				'f1desc': lineArr[12],
				'f2desc': lineArr[13]
			}
	return edges

if __name__ == "__main__":
	print >> sys.stderr, 'usage <edgeFile> <outFile> <intersectionCutoff> <singleFreqCutoff> <lift>'
	edges = edgesFromFile(sys.argv[1])
	print >> sys.stderr, 'got edges'
	graph = analyzeEdges(edges, float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
	print >> sys.stderr, 'constructed graph'
	inOutGraph(graph, sys.argv[2])

