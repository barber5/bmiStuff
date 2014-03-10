from queryByCui import getCuis, r, decomp, compIt
import sys, json

def remCode(code):
	result = set([])
	res = r.hget('codes', code)	
	li = json.loads(decomp(res))	
	for l in li:
		result.add(str(l))
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
			result.add(str(pid))
	return result

def remAllBut():
	codes = ['299', '135', 'random']
	result = set([])
	for code in codes:
		result = result | remCode(code)	
	files = ['pancreatitis.txt']
	for fi in files:
		result = result | remFile(fi)
	print len(result)
	resp = r.hkeys('pats')
	print len(resp)
	dels = set([])
	for pid in resp:
		pid = str(pid)
		if pid not in result:
			#print pid
			dels.add(str(pid))
	for d in dels:
		print 'deleting: '+str(d)
		r.hdel('pats', str(d))

if __name__ == "__main__":
	remAllBut()