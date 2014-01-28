from autismClusters import getInput
import sys, pprint

if __name__ == "__main__":
	patients = getInput(sys.argv[1])
	print len(patients)