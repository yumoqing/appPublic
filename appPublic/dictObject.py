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
		self.__dict__['_kwargs'] = {}
		for k,v in kw.items():
			self._kwargs.update({k:self.__DOitem(v)})
	
	def __getattr__(self, name):
		x = self.__dict__.get(name,None)
		if x:
			return x

		b = self.__dict__.get('_kwargs',None)
		if not b:
			print('Error:_kwargs not in __dict__')
			raise Exception('_kwargs not in __dict__')
		return b.get(name,None)

	def __setattr__(self,name,value):
		self.__setitem__(name,value)

	def __getitem__(self,name):
		x = self.__dict__.get(name,None)
		if x is not None:
			return x

		x  = self._kwargs.get(name,None)
		return x
		
	def __setitem__(self,name,value):
		self._kwargs[name] = value

	def __delitem__(self,name):
		self._kwargs.pop(name)

	def get(self,name,dv=None):
		return self._kwargs.get(name,dv)

	def copy(self):
		return self._kwargs.copy()

	def update(self,d):
		self._kwargs.update(d)

	def keys(self):
		return self._kwargs.keys()

	def items(self):
		return self._kwargs.items()

	def __expr__(self):
		return self._kwargs.__expr__()
		
	def __str__(self):
		return self._kwargs.__str__()

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
