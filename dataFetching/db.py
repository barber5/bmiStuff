import MySQLdb

def getDbs():
	with open('/home/barber5/.my.cnf', 'r') as f:
		for line in f:
			if line.find('user') == 0:
				user = line.split()[-1]
			if line.find('password') == 0:
				password = line.split()[-1]
			if line.find('host') == 0:
				host = line.split()[-1]		
		term_db=MySQLdb.connect(passwd=password,db="terminology3", host=host, user=user)
		stride_db=MySQLdb.connect(passwd=password,db="stride5", host=host, user=user)

		#term_db = MySQLDatabase('terminology3', user=user, host=host, passwd=password)
		#stride_db = MySQLDatabase('stride5', user=user, host=host, passwd=password)

		return term_db, stride_db


def tryQuery(db, query, replace=None):            
    c = db.cursor()
    if replace:
        c.execute(query, replace)
    else:
        c.execute(query)
    result = c.fetchall()
    c.close()
    return result

def getPkFromMapping(row, mapping):
    li = []
    anyVals = False
    for k,v in mapping.iteritems():
        if type(k) == type(23):
            li.append(row[k]) 
            if row[k]:
                anyVals = True   
    if anyVals:
        return tuple(li)
    else:
        return False

def hasSublist(mapping):
    for k,v in mapping.iteritems():
        if type(k) == type('') and type(v) == type([]):
            return True
        elif type(v) == type({}):
            if hasSublist(v):
                return True
    return False



def extractIt(row, mapping, result, idxs, attrName):   
    #print 'ROW IS {}'.format(row) 
    if attrName and attrName not in idxs:
        idxs[attrName] = {}
    if type(result) == type([]):
        pk = getPkFromMapping(row, mapping)
        #print 'PK is {}, attrName is {}'.format(pk, attrName)        
        if pk and pk not in idxs[attrName]:            
            idxs[attrName][pk] = len(result)
            result.append({})    
            #print 'appended {} for PK'        
        if pk:
            pkindex = idxs[attrName][pk]
            #print 'pkindex is {}'.format(pkindex)
            #print 'into this result {}'.format(result)
            if hasSublist(mapping):
                attrName = str(pk)+attrName
            extractIt(row, mapping, result[pkindex], idxs, attrName)

    elif type(result) == type({}):
        pk = getPkFromMapping(row, mapping)
        if hasSublist(mapping):
            if not attrName:
                attrName = ''
            attrName = str(pk)+attrName
        for k,v in mapping.iteritems():
            if(type(k) == type(0)):
                if v not in result:
                    result[v] = row[k]
            elif type(k) == type(''):
                if k not in result:
                    if type(v) == type({}):
                        result[k] = {}
                    elif type(v) == type([]):
                        result[k] = []
                    else:
                        raise Exception('bad name mapping for joiner')
                if type(v) == type({}):
                    extractIt(row, v, result[k], idxs, attrName)
                elif type(v) == type([]):
                    if not attrName:
                        attrName = ''
                    extractIt(row, v[0], result[k], idxs, k + attrName)
                else:
                    raise Exception('bad name mapping for joiner')
    else:
        raise Exception('bad name mapping for joiner')

    


def joinResult(rows, nameMapping):       
    result = {}
    idxs = {}
    attrName = None
    if len(nameMapping) == 1:
        key = nameMapping.keys()[0]
        if type(nameMapping[key]) == type([]):
            attrName = key
            if len(rows) == 0:
                result[key] = []
    for row in rows:
        print row

        extractIt(row, nameMapping, result, idxs, attrName)    
    print 'joinResult result: '+result.__repr__()
    return result


