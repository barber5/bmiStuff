import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))





def subSets(st, size, ignore=set([])):	
	result = set([])
	if size == 0:
		return []	
	for i, s in enumerate(st):		
		if i in ignore:
			continue		

		smallerSets = subSets(st, size-1, ignore | set([i]))			
		if len(smallerSets) == 0:
			result.add((s,))
		smallerSets = set(smallerSets)
		for ss in smallerSets:			
			ss = set(ss)
			ss.add(s)			
				
			nextS = sorted(ss)
			result.add(tuple(nextS))
	result = list(result)
	result = sorted(result)
	return result
		


def candidates(basket, frequent, size):
	sortBasket = sorted(basket)	
	lastResult = 0
	candBuilder = []
	for item in sortBasket:
		if item in frequent:
			candBuilder.append(item)
	i = 1

	while i < size:		
		print 'joining a set of size: '+str(len(candBuilder))
		subsets(candBuilder, size)
		candBuilder = []
		if i < size - 1:
			for cb in candBuilderTmp:
				if cb in frequent:
					candBuilder.append(cb)
		else:
			candBuilder = candBuilderTmp
		i += 1

	return candBuilder
	
		



def mineDict(inp, threshold):
	# get frequent item singletons
	counts = {}
	frequent = set([])
	lastFreq = 0
	size = 1
	for pid, concs in inp.iteritems():
		for ck, count in concs.iteritems():
			if ck not in counts:
				counts[ck] = 0
			counts[ck] += 1
	for ck, freq in counts.iteritems():

		if float(freq) / float(len(inp.keys())) > float(threshold):
			frequent.add(ck)	

	while len(frequent) - lastFreq > 0:
		size += 1
		counts = {}
		lastFreq = len(frequent)
		for pid, concs in inp.iteritems():
			print 'for pid: '+str(pid)+' getting sets of size '+str(size)
			print 'there are '+str(len(concs.keys()))+' concepts for this patient and '+str(len(frequent)) +' frequent items so far'
			cands = candidates(concs.keys(), frequent, size)
			print 'got candidates'
			for c in cands:
				if c not in counts:
					counts[c] = 0
				counts[c] += 1
		for ck, freq in counts.iteritems():
			if float(freq) / float(len(inp.keys())) > float(threshold):
				frequent.add(ck)
		print 'filtered candidates'		

	return frequent




if __name__ == "__main__":
	st = [1, 22, 88]
	print subSets(st, 3)
	