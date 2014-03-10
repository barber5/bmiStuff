from queryByCui import getCuis, r, decomp, compIt
import sys, json

def remCode(code):
	result = set([])
	res = r.hget('codes', code)	
	li = json.loads(decomp(res))	
	for l in li:
		result.add(l)
	return result


def remFile(fName):
	result = set([])
	with open(fName, 'r') as fi:
		firstline = fi.readline()
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split('\t')			
			pid = lineArr[0]
			result.add(pid)
	return result

def remAllBut():
	codes = ['299', '135', 'random']
	result = set([])
	for code in codes:
		result = result | remCode(code)

	
	files = ['pancreatitis.txt']
	for fi in files:
		result = result | remFile(fi)
	resp = r.hkeys('pats')
	print len(resp)
	dels = set([])
	for pid in resp:
		
		if pid not in result:
			#print pid
			dels.add(pid)
	print len(dels)

if __name__ == "__main__":
	remAllBut()