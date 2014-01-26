from relatedTerms import *
from db import *
import sys,pprint
(term_db, stride_db) = getDbs()


def getNotes(pid):
	query = "SELECT n.nid, n.src, n.src_type, n.age, n.timeoffset, n.year, n.duration, n.cpt, n.icd9, m.tid, m.negated, m.familyHistory, t.term FROM note as n inner join mgrep as m on m.nid=n.nid inner join terminology3.terms as t on t.tid=m.tid WHERE n.pid=%s"
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
	print >> sys.stderr, 'got the notes!'
	result = joinResult(rows, nameMapping)
	print >> sys.stderr, 'merged the notes!'
	return result

def getVisits(pid):
	query = "SELECT v.visit, v.src, v.src_type, v.age, v.timeoffset, v.year, v.duration, v.cpt, v.icd9, v.vid from visit as v where v.pid=%s"
	rows = tryQuery(stride_db, query, [pid])
	nameMapping = {
		'visits': [{
			0: 'visit',
			1: 'src',
			2: 'src_type',
			3: 'age',
			4: 'timeoffset',
			5: 'year',
			6: 'duration',
			7: 'cpt',
			8: 'icd9',
			9: 'vid'
		}]
	}
	result = joinResult(rows, nameMapping)
	return result

def getLabs(pid):
	query = "SELECT l.lid, l.src, l.age, l.timeoffset, l.description, l.proc, l.proc_cat, l.line, l.component, l.ord, l.ord_num, l.result_flag, l.ref_low, l.ref_high, l.ref_unit, l.result_inrange, l.ref_norm from lab as l where l.pid=%s"
	rows = tryQuery(stride_db, query, [pid])
	nameMapping = {
		'labs': [{
			0: 'lid',
			1: 'src',
			2: 'age',
			3: 'timeoffset',
			4: 'description',
			5: 'proc',
			6: 'proc_cat',
			7: 'line',
			8: 'component',
			9: 'ord',
			10: 'ord_num',
			11: 'result_flag',
			12: 'ref_low',
			13: 'ref_high',
			14: 'ref_unit',
			15: 'result_inrange',
			16: 'ref_norm'
		}]
	}
	result = joinResult(rows, nameMapping)
	return result

def getPrescriptions(pid):
	query = "SELECT p.rxid, p.src, p.age, p.timeoffset, p.drug_description, p.route, p.order_status, p.ingr_set_id from prescription as p where p.pid=%s"
	rows = tryQuery(stride_db, query, [pid])
	nameMapping = {
		'prescriptions': [{
			0: 'rxid',
			1: 'src',
			2: 'age',
			3: 'timeoffset',
			4: 'drug_description',
			5: 'route',
			6: 'order_status',
			7: 'ingr_set_id'
		}]
	}
	result = joinResult(rows, nameMapping)
	return result
	

def getPatientVec(pid):
	query = "SELECT d.pid, d.patient, d.gender, d.race, d.ethnicity, d.death from demographics as d where d.pid=%s"		
	rows = tryQuery(stride_db, query, [pid])	
	nameMapping = {
		'patients': [{
			0: 'pid',
			1: 'patient',
			2: 'gender',
			3: 'race',
			4: 'ethnicity',
			5: 'death'
		}]
	}
	result = joinResult(rows, nameMapping)
	result['notes'] = getNotes(pid)
	result['prescriptions'] = getPrescriptions(pid)
	result['visits'] = getVisits(pid)
	result['labs'] = getLabs(pid)
	return result

def getMultiplePatientVec(pids):
	result = []
	for pid in pids:
		if os.path.exists(str(pid)+'.txt'):
			print >> sys.stderr, pid
			continue
		next = getPatientVec(pid)
		fi = open(str(pid)+'.txt', 'w')
		fi.write(next.__repr__())
		fi.close()
		result.append(next)
		print >> sys.stderr, pid
	return result

if __name__ == "__main__":
	if len(sys.argv) == 2:
		vec = getPatientVec(sys.argv[1])
	elif len(sys.argv) > 2:
		vec = getMultiplePatientVec(sys.argv[1:])
	pprint.pprint(vec)	