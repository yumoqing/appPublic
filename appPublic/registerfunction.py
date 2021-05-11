
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


def getRegisterFunctionByName(name):
	rf = RegisterFunction()
	return rf.get(name)

def registerFunction(name, func):
	rf = RegisterFunction()
	rf.register(name, func)

if __name__ == '__main__':
	def x(a):
		print('x():a=',a)

	def y(a):
		print('y():a=',a)
	
	def z():
		rf = RegisterFunction()
		for name in ['func1', 'func2' ]:
			f = rf.get(name)
			print(name,f('hahah'))

	rf = RegisterFunction()
	rf.register('func1',x)
	rf.register('func2',y)
	z()
