import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))





def joinSets(st):
	st = sorted(st)
	result = set([])
	for i in range(len(st)):
		for j in range(i+1,len(st)):
			s1 = st[i]
			s2 = st[j]
			if type(s1[0]) == type((4,5)):
				diffs = []
				for k in range(len(s1)):
					if s1[k] != s2[k]:
						diffs.append(k)
					if len(diffs) == 1:
						l = list(s1)
						l.append(s2[diffs[0]])
						l = l.sorted()
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
		candBuilderTmp = joinSets(candBuilder)
		candBuilder = []
		for cb in candBuilderTmp:
			if cb in freq:
				candBuilder.append(cb)
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
		if freq > float(threshold) / float(len(inp.keys())):
			frequent.add(ck)


	while len(frequent) - lastFreq > 0:
		size += 1
		counts = {}
		lastFreq = len(frequent)
		for pid, concs in inp.iteritems():
			cands = candidates(concs.keys(), frequent, size)
			for c in cands:
				if c not in counts:
					counts[c] = 0
				counts[c] += 1
		for ck, freq in counts.iteritems():
			if freq > float(threshold) / float(len(inp.keys())):
				frequent.add(ck)


	return frequent




if __name__ == "__main__":
	print 'hi'