from queryByCui import getCuis, r, decomp, compIt

def remCode(code):
	res = r.hget('codes', code)	
	li = json.loads(decomp(res))	
	for l in li:
		print l

if __name__ == "__main__":
	remCode(sys.argv[1])