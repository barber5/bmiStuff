import sys, pprint

def getPredPowers(fileName):
	result = {}
	with open(fileName, 'r') as fi:
		while True:
			line = fi.readline().strip()
			if line == '':
				break
			lineArr = line.split('\t')
			print lineArr
			feat = lineArr[0]
			imp = lineArr[1]
			if feat.find('code:') == 0:
				if 'code' not in result:
					result['code'] = []
				result['code'].append(imp)
			if feat.find('cid:') == 0:
				if 'cid' not in result:
					result['cid'] = []
				result['cid'].append(imp)
			if feat.find('prescription:') == 0:
				if 'prescription' not in result:
					result['prescription'] = []
				result['prescription'].append(imp)
			if feat.find('lab:') == 0:
				if 'lab' not in result:
					result['lab'] = []
				result['lab'].append(imp)

	return result

if __name__ == "__main__":
	pp = getPredPowers(sys.argv[1])
	pprint.pprint(pp)