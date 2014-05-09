import sys,os, pprint, json, random, pprint, math, time
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
sys.path.append(os.path.realpath('../fpmining'))
sys.path.append(os.path.realpath('./fpmining'))


from ast import literal_eval as make_tuple
from pygraphml.GraphMLParser import *
from pygraphml.Graph import *
from pygraphml.Node import *
from pygraphml.Edge import *
from network import getWeightedGraph


def inOutGraph(graphDict, wg, gFile, singleton):
	g = Graph()
	nDict = {}
	for node, meta in graphDict.iteritems():	
		if not singleton and len(meta['out']) == 0:
			continue	
		n = g.add_node(str(node))			
		n['freq'] = meta['freq']
		n['type'] = node[0][0]
		n['enrichment'] = meta['enrichment']	
		if str(node) in wg:
			n['community'] = wg[str(node)]
		else:
			n['community'] = -1
		nDict[node] = n
	for node, meta in graphDict.iteritems():
		if node not in nDict:
			continue
		n = nDict[node]			
		for node2, edgeMeta in meta['out'].iteritems():			
			n2 = nDict[node2]
			e = g.add_edge(n, n2, directed=True)
			e['lift'] = edgeMeta['lift']
			e['lambda'] = edgeMeta['lambda']
			e['lambdaFirst'] = edgeMeta['lambdaFirst']		
			e['avgOffset'] = edgeMeta['avgOffset']	
			e['intersection'] = edgeMeta['intersection']
			e['conf'] = edgeMeta['conf']
	parser = GraphMLParser()
	parser.write(g, 'tmp/'+gFile)
	with open(gFile, 'w') as fi:
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
				elif line.find('attr.name="conf"') != -1:
					fi.write('    <key attr.name="conf" attr.type="double" id="conf"/>\n')
				else:
					fi.write(line)



def analyzeEdges(edges, intersectionCutoff=.05, cutoff=.01, lift=1.0, conf=0.5):
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
				'out': {},
				'adjacent': {},
				'desc': meta['f1desc'],
				'freq': meta['f1freq'],
				'enrichment': meta['f1enrich']
			}
		if f2 not in graph:
			graph[f2] = {				
				'out': {},
				'adjacent': {},
				'desc': meta['f2desc'],
				'freq': meta['f2freq'],
				'enrichment': meta['f2enrich']
			}
		
		if (meta['lift'] > lift or meta['lift'] < -lift) and meta['intersection'] > intersectionCutoff:
			c12 = float(meta['intersection'])/float(meta['f2freq'])  # P(1|2) = P(1,2)/P(2)   2 -> 1
			c21 = float(meta['intersection'])/float(meta['f1freq'])  # P(2|1) = P(1,2)/P(1)   1 -> 2
			if c12 > c21:
				if c12 > conf:
					graph[f2]['out'][f1] = {
						'lambda': meta['lambda'],
						'lambdaFirst': meta['lambdaFirst'],
						'lift': meta['lift'],
						'avgOffset': meta['avgOffset'],
						'intersection': meta['intersection'],
						'conf': c12
					}
			else:
				if c21 > conf:
					graph[f1]['out'][f2] = {
						'lambda': meta['lambda'],
						'lambdaFirst': meta['lambdaFirst'],
						'lift': meta['lift'],
						'avgOffset': meta['avgOffset'],
						'intersection': meta['intersection'],
						'conf': c21
					}

			'''
			if meta['lambdaFirst'] > 0:
				graph[f1]['out'][f2] = {
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
		'''	
		
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

def findTriangles(node, meta, graph, original, steps, path, maxSteps):
	result = []	
	path.append(node)
	if steps <= maxSteps and node == original and steps > 0:		
		result.append(path)			
		return result
	elif steps == maxSteps:
		return result
	for m, outMeta in meta['out'].iteritems():
		pathNext = []
		for p in path:
			pathNext.append(p)
		fwdResult = findTriangles(m, graph[m], graph, original, steps+1, pathNext, maxSteps)		
		for fr in fwdResult:
			result.append(fr)		
	return result

def breakTriangle(tri, graph):
	minInt = float('inf')
	minE = None
	for i in range(len(tri)-1):
		n1 = tri[i]
		n2 = tri[i+1]
		gn1 = graph[n1]
		gn2 = graph[n2]
		
		e12 = gn1['out'][n2]
		i1 = e12['intersection']
		if i1 < minInt:
			minInt = i1
			minE = (n1, n2)
	n1 = minE[0]
	n2 = minE[1]
	gn1 = graph[n1]
	gn2 = graph[n2]
	del gn1['out'][n2]			
	return 1


def dfs_recurs(graph, m, visited, t, timings, backPointers):
	t+=1
	mn = graph[m]
	#print 'start: '+str(m)+' '+str(t)
	visited[m] = True
	timings[m] = {}
	timings[m]['start'] = t
	for next in mn['out']:
		if next in visited and 'end' in timings[next]:
			# cross edge, no cycle detected
			#print 'cross'
			continue
		backPointers[next] = m
		if next in visited and 'end' not in timings[next]:
			# back edge
			print 'back edge detected'
			return (next, backPointers)
		fwdResult = dfs_recurs(graph, next, visited, t, timings, backPointers)
		if fwdResult:
			return fwdResult
	#print 'end: '+str(m)+' '+str(t)
	timings[m]['end'] = t
	

def dfs(graph):
	visited = {}
	timings = {}
	backPointers = {}
	for m in graph:
		if m in visited:
			continue
		
		fwdResult = dfs_recurs(graph, m, visited, 0, timings, backPointers)
		if fwdResult:
			return fwdResult
	return (None, {})

	

def removeTriangles(graph):
	total = 0
	nodes = len(graph.keys())
	while True:
		print >> sys.stderr, 'performing dfs'
		(o,backPointers) = dfs(graph)
				
		#pprint.pprint(backPointers)		
		if o == None:
			break
		next = o			
		
		path = [o]
		while True:
			print next
			bpn = backPointers[next]			
			path.append(bpn)
			if bpn == o:
				break
			next = bpn
		print >> sys.stderr, 'removing a cycle of length '+str(len(path))+' '+str(total)+' removed so far'
		path = [ p for p in reversed(path)]
		total += breakTriangle(path, graph)	



	

if __name__ == "__main__":
	print >> sys.stderr, 'usage <edgeFile> <outFile> <intersectionCutoff> <singleFreqCutoff> <lift> <confidence cutoff> (optional -sing to include singleton nodes)'
	edges = edgesFromFile(sys.argv[1])
	if '-sing' in sys.argv:
		singleton = True
	else:
		singleton = False

	print >> sys.stderr, 'got edges'
	graph = analyzeEdges(edges, float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]))
	wg = getWeightedGraph(graph)
	print >> sys.stderr, 'constructed graph'	
	removeTriangles(graph)
	
	inOutGraph(graph, wg, sys.argv[2], singleton)

