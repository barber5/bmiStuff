import sys,os, pprint, json, random, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
sys.path.append(os.path.realpath('../fpmining'))
sys.path.append(os.path.realpath('./fpmining'))

from queryByCui import r, decomp, compIt
from getTermByID import getTerm, getTermCui, getIngredients, getIngredient, getLab, getConcept

# patients is pid -> {pid, src_type, labs -> [{age, , component, description, lid, line, ord, ord_num, proc, proc_cat, ref_high, ref_low, ref_norm, ref_unit, result_flag, result_inrange, src, timeoffset}], notes -> [{age, cpt, duration, icd9, nid, pid, src, src_type, timeoffset, year, terms -> [{cui, familyHistory, negated, nid, termid, tid}]}], prescriptions -> [{age, drug_description, ingr_set_id, order_status, pid, route, rxid, src, timeoffset}], visits -> [{age, cpt, duration, icd9, pid, src, src_type, timeoffset, year}] }
def beforeAndAfter(enrichments, featIdx, patients, codes):
	for pid, resp in patients.iteritems():
		minOffset = float('inf')
		for v in resp['visits']:
			icd9s = v['icd9']
			icd9sArr = icd9s.split(',')
			icd9sArr = [str(i) for i in icd9sArr]
			for code in codes:
				if code in icd9sArr:
					if v['timeoffset'] < minOffset:
						minOffset = v['timeoffset']
		print minOffset

if __name__ == "__main__":
	print 'hi'