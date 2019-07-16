import numpy as np
import random
 
class Distribution:
	def __init__(self,vl,pl=[],dtype=np.int):
		self.dtype = dtype
		self.cnt = len(vl)
		vlen = len(vl)
		plen = len(pl)
		sp = sum(pl)
		if plen > vlen:
			pl = pl[:vlen]
			plen = vlen
		if sp > 1.0:
			raise Exception("Probability > 1")
		if plen < vlen:
			pv = 1.0 - sp
			n = vlen - plen
			p = pv / n
			for i in range(n-1,vlen):
				pl.append(p)
		self.vl = vl
		self.pl = pl
		vp = []
		vp = [1,]
		i = vlen - 1
		while  i > 0:
			vp.append(vp[vlen - i  - 1] - pl[i])
			i -= 1
		vp.reverse()
		self.vp = vp

	def distri(self,value):
		for v in self.vl:
			print(v,(len([i for i in value if v == i])*1.0) /(len(value)*1.0))
			
	def func(self,v):
		i = 0
		while i < self.cnt:
			if v < self.vp[i]:
				return self.vl[i]
			i += 1
		return self.vp[self.cnt -1]

	def generator(self,count):
		a = np.random.rand(count)
		func = np.frompyfunc(self.func,1,1)
		return func(a)

if __name__ == '__main__':
	d1 = Distribution([1,2,3,4],[.5,.24])
	v = d1.generator(100000)
	print('v=',v)
	
	print(d1.distri(v))
	v = d1.generator(2000000)
	print(d1.distri(v))
