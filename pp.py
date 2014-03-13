import sys, pprint

def getPredPowers(fileName):
	result = {}
	with open(fileName, 'r') as fi:
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split('\t')			
			feat = lineArr[0]
			imp = float(lineArr[1])
			if feat.find('code:') == 0:
				if 'code' not in result:
					result['code'] = 0
				result['code'] += imp
			if feat.find('cid:') == 0:
				if 'cid' not in result:
					result['cid'] = 0
				result['cid'] += imp
			if feat.find('prescription:') == 0:
				if 'prescription' not in result:
					result['prescription'] = 0
				result['prescription'] += imp
			if feat.find('lab:') == 0:
				if 'lab' not in result:
					result['lab'] = 0
				result['lab'] += imp

	return result

if __name__ == "__main__":
	pp = getPredPowers(sys.argv[1])
	pprint.pprint(pp)