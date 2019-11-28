
from functools import partial
from appPublic.Singleton import SingletonDecorator

@SingletonDecorator
class RegisterFunction:
	def __init__(self):
		self.registKW = {}

	def register(self,name,func):
		self.registKW[name] = func
	
	def get(self,name):
		return self.registKW.get(name,None)

