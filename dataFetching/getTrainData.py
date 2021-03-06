from queryByCui import r, decomp, compIt
import sys, random, json


def getPidsByCode(code1, code2, num1, num2):
	res1 = r.hget('codes', code1)
	li1 = json.loads(decomp(res1))
	res2 = r.hget('codes', code2)
	li2 = json.loads(decomp(res2))
	result = {}
	for i in range(num1):
		next = str(random.choice(li1))
		result[next] = 1
	for i in range(num2):
		next = str(random.choice(li2))
		result[next] = 0
	return result

if __name__ == "__main__":
	print getPidsByCode(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
