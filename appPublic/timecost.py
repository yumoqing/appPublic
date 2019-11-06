import time
import datetime
from .Singleton import SingletonDecorator

timerecord = {}

class TimeCost:
	def __init__(self,name):
		self.name = name
	
	def __enter__(self):
		self.begin_time = time.time()
	
	def __exit__(self,*args):
		self.end_time = time.time()
		d = timerecord.get(self.name,[])
		d.append(self.end_time - self.begin_time)
		timerecord[self.name] = d

	def clear(self):
		timerecord = {}

	def getTimeCost(self,name):
		x = timerecord.get(name,[])
		if len(x) == 0:
			return 0,0,0
		return len(x), sum(x), sum(x)/len(x)
	
	def show(self):
		print('TimeCost ....')
		for name in timerecord.keys():
			print(name, * self.getTimeCost(name))

