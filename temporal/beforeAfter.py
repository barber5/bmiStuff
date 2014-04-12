import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
sys.path.append(os.path.realpath('../fpmining'))
sys.path.append(os.path.realpath('./fpmining'))

from queryByCui import r, decomp, compIt
from getTermByID import getTerm, getTermCui, getIngredients, getIngredient, getLab, getConcept
from ast import literal_eval as make_tuple
from mineConcepts import getFromFile

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def beforeAndAfter(enrichments, codes, patients):
	total = 0
	featOffsets = {}
	for pid, dd in patients.iteritems():
		myCodes = []
		minOffset = float('inf')
		for v in dd['visits']:			
			icd9s = v['icd9']
			if icd9s == '':
				continue
			icd9sArr = icd9s.split(',')			
			icd9sArr = [str(i) for i in icd9sArr]	
			myCodes.extend(icd9sArr)		
			for code in codes:
				if code in icd9sArr:										
					if v['timeoffset'] < minOffset:
						minOffset = v['timeoffset']
		if not minOffset < float('inf'):
			continue
		for n in dd['notes']:
			delt = float(n['timeoffset']) - minOffset
			for term in n['terms']:
				cid = term['cid']
				concept = term['concept']			
				cidKey = ('cid', cid, term['negated'], term['familyHistory'])
				if cidKey not in nextPerson:
					nextPerson[cidKey] = 0
					featIdx[cidKey] = term['concept']
				if cidKey in enrichments:
					if cidKey not in featOffsets:
						featOffsets[cidKey] = []

					featOffsets[cidKey].append(delt)
				nextPerson[cidKey] += 1
		for l in dd['labs']:
			if 'ord_num' not in l or not l['ord_num'] or l['ord_num'] == '':
				continue
			if 'result_flag' not in l or not l['result_flag'] or l['result_flag'] == '':
				val = 'normal'
			else:
				val = l['result_flag']
			delt = float(l['timeoffset']) - minOffset
			labKey = ('lab', l['proc'], l['component'], val)
			if labKey not in nextPerson:
				nextPerson[labKey] = 0
				featIdx[labKey] = getLab(l['component'])
			if labKey in enrichments:
				if labKey not in featOffsets:
					featOffsets[labKey] = []
				featOffsets[labKey].append(delt)
			nextPerson[labKey] += 1



		for p in dd['prescriptions']:	
			delt = float(p['timeoffset']) - minOffset		
			ings = getIngredients(p['ingr_set_id'])
			for i in ings:				
				ingKey = ('prescription', i)
				if ingKey not in nextPerson:
					nextPerson[ingKey] = 0
					featIdx[ingKey] = getIngredient(i)
				if ingKey in enrichments:
					if ingKey not in featOffsets:
						featOffsets[ingKey] = []
					featOffsets[ingKey].append(delt)
				nextPerson[ingKey] += 1
	
	return featOffsets

def getEnrichments(enrFile):
	enrichments = {}
	with open(enrFile, 'r') as fi:
		while True:
			line = fi.readline()
			if line == '':
				break
			lineArr = line.split('\t')
			tupStr = lineArr[0]
			enr = float(lineArr[1])
			caseCnt = int(lineArr[2])
			controlCnt = int(lineArr[3])
			desc = lineArr[4]	
			feat = make_tuple(tupStr)		
			enrichments[feat] = {
				'enrichment': enr,
				'case': caseCnt,
				'control': controlCnt,
				'description': desc
			}
	return enrichments

def getCodes(codeFile):
	codes = []
	with open(codeFile) as fi:
		while True:
			line = fi.readline()
			if line == '':
				break
			code = line.split(':')[1]
			codes.append(code)

	return codes

def getPatients(num, patFile):
	return getFromFile(num, patFile)

if __name__ == "__main__":
	print 'usage: <enrichmentsFile> <codeFile> <patientFile> <numPatients>'
	enr = getEnrichments(sys.argv[1])
	codes = getCodes(sys.argv[2])
	pats = getPatients(int(sys.argv[4]), sys.argv[3])
	beforeAndAfter(enr, codes, pats)