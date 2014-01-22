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
	return c.fetchall()

