from relatedTerms import *
from db import *
import sys,pprint
(term_db, stride_db) = getDbs()

def getPatientVec(pid):
	query = "SELECT n.pid, n.patient, n.nid, n.src, n.src_type, n.age, n.timeoffset, n.year, n.duration, n.cpt, n.icd9, m.tid, m.negated, m.familyHistory, t.term, v.visit, v.src, v.src_type, v.age, v.timeoffset, v.year, v.duration, v.cpt, v.icd9, v.vid, l.lid, l.src, l.age, l.timeoffset, l.description, l.proc, l.proc_cat, l.line, l.component, l.ord, l.ord_num, l.result_flag, l.ref_low, l.ref_high, l.ref_unit, l.result_inrange, l.ref_norm, p.rxid, p.src, p.age, p.timeoffset, p.drug_description, p.route, p.order_status, p.ingr_set_id, d.gender, d.race, d.ethnicity, d.death FROM note as n left outer join mgrep as m on n.nid=m.nid left outer join visit as v on v.pid=n.pid left outer join prescription p on p.pid=n.pid left outer join lab l on l.pid=n.pid left outer join demographics d on d.pid=n.pid left outer join terminology3.terms as t on t.tid=m.tid WHERE n.pid=%s"
	rows = tryQuery(stride_db, query, [pid])
	nameMapping = {
		'patients': [{
			0: 'pid',
			1: 'patient',
			50: 'gender',
			51: 'race',
			52: 'ethnicity',
			53: 'death',
			'notes': [{
				2: 'nid',
				3: 'src',
				4: 'src_type',
				5: 'age',
				6: 'timeoffset',
				7: 'year',
				8: 'duration',
				9: 'cpt',
				10: 'icd9',
				'terms': [{
					11: 'tid',
					12: 'negated',
					13: 'familyHistory',
					14: 'term'
				}]
			}],
			'visits': [{
				15: 'visit',
				16: 'src',
				17: 'src_type',
				18: 'age',
				19: 'timeoffset',
				20: 'year',
				21: 'duration',
				22: 'cpt',
				23: 'icd9',
				24: 'vid'
			}],
			'labs': [{
				25: 'lid',
				26: 'src',
				27: 'age',
				28: 'timeoffset',
				29: 'description',
				30: 'proc',
				31: 'proc_cat',
				32: 'line',
				33: 'component',
				34: 'ord',
				35: 'ord_num',
				36: 'result_flag',
				37: 'ref_low',
				38: 'ref_high',
				39: 'ref_unit',
				40: 'result_inrange',
				41: 'ref_norm'
			}],
			'prescriptions': [{
				42: 'rxid',
				43: 'src',
				44: 'age',
				45: 'timeoffset',
				46: 'drug_description',
				47: 'route',
				48: 'order_status',
				49: 'ingr_set_id'
			}]
		}]
	}
	result = joinResult(rows, nameMapping)
	return result

def getMultiplePatientVec(pids):
	result = []
	for pid in pids:
		result.append(getPatientVec(pid))
		print >> sys.stderr, pid
	return result

if __name__ == "__main__":
	if len(sys.argv) == 2:
		vec = getPatientVec(sys.argv[1])
	elif len(sys.argv) > 2:
		vec = getMultiplePatientVec(sys.argv[1:])
	pprint.pprint(vec)	