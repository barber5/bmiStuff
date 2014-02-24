import sys,os, pprint
sys.path.append(os.path.realpath('../tempClustering'))
sys.path.append(os.path.realpath('./tempClustering'))
sys.path.append(os.path.realpath('../dataFetching'))
sys.path.append(os.path.realpath('./dataFetching'))
from queryByCode import getPids

def expForCode(code):
	pids = getPids(code)
	print pids

if __name__ == "__main__":
	expForCode(int(sys.argv[1]))