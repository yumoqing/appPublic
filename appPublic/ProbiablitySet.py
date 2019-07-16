import numpy as np
import random
from Distribution import Distribution
class ProbabilitySet:
	def __init__(self,dset,p):
		self.dset = dset
		self.probiablity = p
		
	def dataset(self):
		dl = Distribution([1,0],[self.probiablity,])
		v = dl.generator(len(self.dset))
		m = []
		for i in range(len(self.dset)):
			if v[i] == 1:
				m.append(self.dset)
		return m
		
if __name__ == '__main__':
	from timecost import TimeCost
	dset = range(10000000)
	pp = [0.1,0.22,0.334,0.88,0.93]
	tc = TimeCost()
	for p in pp:
		tc.begin('dataset() %f' % p)
		ps = ProbablitySet(dset,p)
		d = ps.dataset()
		tc.end('dataset() %f' % p)
	
	tc.show()
