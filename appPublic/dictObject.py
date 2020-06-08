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

class DictObject(dict):
	def __init__(self,**kw):
		dict.__init__(self, **kw)
		for k,v in kw.items():
			self.update({k:self.__DOitem(v)})
	
	def __getattr__(self, name):
		return self.get(name,None)

	def __setattr__(self,name,value):
		self[name] = value

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
			try:
				d = DictObject(**i)
				return d
			except Exception as e:
				print("****************",i,"*******dictObject.py")
				raise e
		if type(i) is type([]):
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
