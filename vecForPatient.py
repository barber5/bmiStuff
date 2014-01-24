from relatedTerms import *
from db import *
import sys,pprint
(term_db, stride_db) = getDbs()


def getNotes(pid):
	query = "SELECT n.nid, n.src, n.src_type, n.age, n.timeoffset, n.year, n.duration, n.cpt, n.icd9, m.tid, m.negated, m.familyHistory, t.term FROM notes as n inner join mgrep as m on m.nid=n.nid inner join terminology3.terms as t"
	nameMapping = {
		'notes': [{
			0: 'nid',
			1: 'src',
			2: 'src_type',
			3: 'age',
			4: 'timeoffset',
			5: 'year',
			6: 'duration',
			7: 'cpt',
			8: 'icd9',
			'terms': [{
				9: 'tid',
				10: 'negated',
				11: 'familyHistory',
				12: 'term'
			}]
		}]
	}
	rows = tryQuery(stride_db, query, [pid])
	result = joinResult(rows, nameMapping)
	return result

def getPatientVec(pid):
	query = "SELECT v.pid, v.patient, v.visit, v.src, v.src_type, v.age, v.timeoffset, v.year, v.duration, v.cpt, v.icd9, v.vid, l.lid, l.src, l.age, l.timeoffset, l.description, l.proc, l.proc_cat, l.line, l.component, l.ord, l.ord_num, l.result_flag, l.ref_low, l.ref_high, l.ref_unit, l.result_inrange, l.ref_norm, p.rxid, p.src, p.age, p.timeoffset, p.drug_description, p.route, p.order_status, p.ingr_set_id, d.gender, d.race, d.ethnicity, d.death FROM visit as v left outer join prescription p on p.pid=v.pid left outer join lab l on l.pid=v.pid left outer join demographics d on d.pid=v.pid  WHERE v.pid=%s"
	
	rows = tryQuery(stride_db, query, [pid])
	print >> sys.stderr, 'got the rows!'
	nameMapping = {
		'patients': [{
			0: 'pid',
			1: 'patient',
			37: 'gender',
			38: 'race',
			39: 'ethnicity',
			40: 'death',			
			'visits': [{
				2: 'visit',
				3: 'src',
				4: 'src_type',
				5: 'age',
				6: 'timeoffset',
				7: 'year',
				8: 'duration',
				9: 'cpt',
				10: 'icd9',
				11: 'vid'
			}],
			'labs': [{
				12: 'lid',
				13: 'src',
				14: 'age',
				15: 'timeoffset',
				16: 'description',
				17: 'proc',
				18: 'proc_cat',
				19: 'line',
				20: 'component',
				21: 'ord',
				22: 'ord_num',
				23: 'result_flag',
				24: 'ref_low',
				25: 'ref_high',
				26: 'ref_unit',
				27: 'result_inrange',
				28: 'ref_norm'
			}],
			'prescriptions': [{
				29: 'rxid',
				30: 'src',
				31: 'age',
				32: 'timeoffset',
				33: 'drug_description',
				34: 'route',
				35: 'order_status',
				36: 'ingr_set_id'
			}]
		}]
	}
	result = joinResult(rows, nameMapping)
	result['notes'] = getNotes(pid)
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