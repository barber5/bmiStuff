from queryByCui import getCuis, r, decomp, compIt
import sys, json

def remCode(code):
	result = set([])
	res = r.hget('codes', code)	
	li = json.loads(decomp(res))	
	for l in li:
		result.add(l)
	return result

def remAllBut():
	codes = ['299', '135', 'random']
	result = set([])
	for code in codes:
		result = result | remCode(code)
	print len(result)
	files = 'pancreatitis.txt'

if __name__ == "__main__":
	remAllBut