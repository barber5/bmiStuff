from queryByCui import r, decomp, compIt
import sys


def getPidsByCode(code):
	res = r.hget('codes', code)
	return decomp(res)

# this will take an icd9 code and output all of the pids 
# that are in the cache that have the given code
if __name__ == "__main__":
	print getPidsByCode(sys.argv[1])
