import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))





def joinSets(st):	
	st = sorted(st)
	print st
	result = set([])
	for i in range(len(st)):
		for j in range(i+1, len(st)):
		
			s1 = st[i]
						
			if type(s1[0]) == type((4,5)):
				if i == len(st) - 1:
					continue			
				s2 = st[j]			
				print '\n'
				print s1
				print s2						
				s = set(s1) | set(s2)
				if len(s) != len(s1) + 1:
					print 'nope'
					continue
				l = list(s)
				l = sorted(l)
				tup = tuple(l)
				print tup
				result.add(tup)
				
			else:
				
				s2 = st[j]
				l = [s1, s2]
				l = sorted(l)
				tup = tuple(l)
				result.add(tup)
	l = list(result)
	l = sorted(l)
	return l
		


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
	st = [(1,3), (20,4), (119, 12), ('x', 43)]
	s1 = joinSets(st)
	print s1
	s2 = joinSets(s1)
	print s2
	s3 = joinSets(s2)
	print s3