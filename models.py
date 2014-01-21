from peewee import *

mysql_db = None
with open('~/.my.cnf', 'r') as f:
	for line in f:
		if line.find('user') == 0:
			user = line.split()[-1]
		if line.find('password') == 0:
			password = line.split()[-1]
		if line.find('host') == 0:
			host = line.split()[-1]

	term_db = MySQLDatabase('terminology3', user=user, host=host, password=password)
	stride_db = MySQLDatabase('stride5', user=user, host=host, password=password)