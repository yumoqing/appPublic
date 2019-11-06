import time
import datetime
# from .Singleton import SingletonDecorator

BEGIN=0
END=1

def datetimeStr(t):
	dt = time.localtime(t)
	return time.strftime('%Y-%m-%d %H:%M:%S',dt)

class TimeCost:
	timerecord = {}
	def __init__(self,name):
		self.name = name
	
	def __enter__(self):
		self.begin_time = time.time()
	
	def __exit__(self):
		self.end_time = time.time()
		d = self.timerecord.get('name',[])
		d.append(self.end_time - self.begin_time)

	def getTimeCost(self,name):
		x = self.timerecord.get('name',[])
		return len(x), sum(x), sum(x)/len(x)
	
	def show(self):
		for name in self.timerecord.keys():
			print(name, * self.getTimeCost(name))

