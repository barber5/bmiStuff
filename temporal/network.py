import sys,os, pprint, json, random, pprint, math, time, operator
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
sys.path.append(os.path.realpath('../fpmining'))
sys.path.append(os.path.realpath('./fpmining'))
import community

from ast import literal_eval as make_tuple
import networkx as nx


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
	
def getWeightedGraph(graph):
	result=nx.Graph()
	for f, meta in graph.iteritems():
		if len(meta['out']) > 0:
			result.add_node(str(f), desc=meta['desc'], freq=meta['freq'], enrichment=meta['enrichment'])
	
	for f,meta in graph.iteritems():			
		for f2, edgeMeta in meta['out'].iteritems():
			result.add_weighted_edges_from([(str(f), str(f2), edgeMeta['lift'])])
	partition = community.best_partition(result)
	parts = {}
	partCounts = {}
	partList = {}
	for p, m in partition.iteritems():
		print p
		print m
		if m not in partCounts:
			partCounts[m] = 0
			partList[m] = []
		partCounts[m] += 1
		partList[m].append(p)

	sorted_x = reversed(sorted(partCounts.iteritems(), key=operator.itemgetter(1)))
	for x in sorted_x:
		print x



	return partition

if __name__ == "__main__":
	print >> sys.stderr, 'usage <edgeFile> <intersectionCutoff> <singleFreqCutoff> <lift> <confidence cutoff>'
	edges = edgesFromFile(sys.argv[1])
	print >> sys.stderr, 'got edges'
	graph = analyzeEdges(edges, float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
	print >> sys.stderr, 'constructed graph'	
	wGraph = getWeightedGraph(graph)
	
	

