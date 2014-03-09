from queryByCui import r, decomp, compIt
import sys, random, json


def getPidsByCode(code1, code2, num1, num2):
	res1 = r.hget('codes', code1)
	li1 = decomp(res1)
	res2 = r.hget('codes', code2)
	li2 = json.loads(decomp(res2))
	pos = {}
	neg = {}
	for i in range(num1):
		next = random.choice(li1)
		pos[next] = 1
	for i in range(num2):
		next = random.choice(li2)
		neg[next] = 0
	return (pos, neg)

if __name__ == "__main__":
	print getPidsByCode(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
