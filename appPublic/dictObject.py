import json
from json import JSONEncoder

def multiDict2Dict(md):
	ns = {}
	for k,v in md.items():
		ov = ns.get(k,None)
		if ov is None:
			ns[k] = v
		elif type(ov) == type([]):
			ov.append(v)
			ns[k] = ov
		else:
			ns[k] = [ov,v]
	return ns

class DictObject:
	def __init__(self,**kw):
		self.__kw = {}
		for k,v in kw.items():
			self.update({k:self.__DOitem(v)})
	
	def update(self,kw):
		self.__kw.update(kw)

	def clear(self):
		return self._kw.clear()

	def get(self,name,default):
		return self._kw.get(name,default)

	def pop(self):
		return self.__kw.pop()

	def popitem(self,g):
		return self.__kw.popitem(g)

	def items(self):
		return self.__kw.items()

	def keys(self):
		return self.__kw.keys()

	def values(self):
		return self.__kw.values()

	def __getitem__(self,name):
		return self.__kw.get(name)
	
	def __setitem__(self,name,value):
		self.__kw[name] = value

	def __getattr__(self, name):
		if self.__kw.get(name):
			return self.__kw.get(name)
		return None

	def __str__(self):
		return str(self.__kw)

	def __expr__(self):
		return self.__kw.__expr__()

	def copy(self):
		return {k:v for k,v in self.__kw.items()}

	@classmethod
	def isMe(self,name):
		return name == 'DictObject'
		
	def __DOArray(self,a):
		b = [ self.__DOitem(i) for i in a ]
		return b
	
	def __DOitem(self, i):
		if isinstance(i,DictObject):
			return i
		if isinstance(i,dict):
			i = {k:v for k,v in i.items() if isinstance(k,str)}
			try:
				d = DictObject(**i)
				return d
			except Exception as e:
				print("****************",i,"*******dictObject.py")
				raise e
		if type(i) == type([]) or type(i) == type(()) :
			return self.__DOArray(i)
		return i

class DictObjectEncoder(JSONEncoder):
	def default(self, o):
		return o._kwargs

def dictObjectFactory(_klassName__,**kwargs):
	def findSubclass(_klassName__,klass):
		for k in klass.__subclasses__():
			if k.isMe(_klassName__):
				return k
			k1 = findSubclass(_klassName__,k)
			if k1 is not None:
				return k1
		return None
	try:
		if _klassName__=='DictObject':
			return DictObject(**kwargs)
		k = findSubclass(_klassName__,DictObject)
		if k is None:
			return DictObject(**kwargs)
		return k(**kwargs)
	except Exception as e:
		print("dictObjectFactory()",e,_klassName__)
		raise e
