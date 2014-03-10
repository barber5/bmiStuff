from queryByCui import getCuis, r, decomp, compIt
import sys, json

def remCode(code):
	res = r.hget('codes', code)	
	li = json.loads(decomp(res))	
	for l in li:
		print l

def remAllBut():
	codes = ['299', '135', 'random']
	files = 'pancreatitis.txt'

if __name__ == "__main__":
	remCode(sys.argv[1])