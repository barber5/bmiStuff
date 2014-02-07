import redis, sys


def loadRedis(filename, startpoint):
	r = redis.StrictRedis(host='localhost', port=6379, db=0)
	i = 0
	fi = open(filename, 'r')
	while True:
		line = fi.readline()
		if line == '':
			break
		lineArr = line.split('\t')
		key = lineArr[0]
		val = ' '.join(lineArr[1:]).strip()	
		r.lpush(key, val)
		i+=1
		if i%1000 == 0:
			print i

	fi.close()

if __name__ == "__main__":
	loadRedis(sys.argv[1], int(sys.argv[2]))