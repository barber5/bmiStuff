import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))





def joinSets(st):
	st = sorted(st)
	result = set([])
	for i in range(len(st)):
		j = i+1
		s1 = st[i]
		s2 = st[j]			
		if type(s1[0]) == type((4,5)):
			diffs = []
			for k in range(len(s1)):
				if s1[k] != s2[k]:
					diffs.append(k)
				if len(diffs) == 1:
					s = set(s1) | set(s2)
					l = list(s)
					l = sorted(l)
					tup = tuple(l)
					result.add(tup)
		else:
			l = [s1, s2]
			l = sorted(l)
			tup = tuple(l)
			result.add(tup)
	return list(result)
		


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
		candBuilderTmp = joinSets(candBuilder)
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
	st = [(1,3), (20,4), (119, 12)]
	print candidates(st, st, 2)