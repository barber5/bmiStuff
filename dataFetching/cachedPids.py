from queryByCui import r, decomp, compIt
import sys


def getPidsByCode(code):
	res = r.hget('codes', code)
	return decomp(res)

if __name__ == "__main__":
	print getPidsByCode(sys.argv[1])
