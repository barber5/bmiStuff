import sys, pprint

def getInput(fileName):
	patients = {}
	with open(fileName, 'r') as fi:
		while True:
			line = fi.readline()
			if line == '':
				break
			lineArr = line.strip().split('\t')			
			record = {
				'id': lineArr[0],
				'age': int(lineArr[1]),
				'offset': float(lineArr[2]),
				'year': lineArr[3],
				'conditions': []			
			}
			if len(lineArr) > 4:
				record['conditions'] = lineArr[4].split(',')
			if record['id'] not in patients:
				patients[record['id']] = {}
			if record['offset'] not in patients[record['id']]:
				patients[record['id']][record['offset']] = record
		fi.close()
	return patients



if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	pprint.pprint(patients)