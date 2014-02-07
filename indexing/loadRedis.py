import redis


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
		val = ' '.join(lineArr[1:])		
		r.lpush(key, val)
		i+=1
		print i

	fi.close()

if __name__ == "__main__":
	loadRedis(sys.argv[1], int(sys.argv[2]))