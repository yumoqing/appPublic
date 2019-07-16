import os,sys
from folderUtils import ProgramPath

class PublicData :
	def __init__(self) :
		p = ProgramPath()
		# print p
		self.ProgramPath = os.path.dirname(ProgramPath())

	def set(self,name,value) :
		setattr(self,name,value)

	def get(self,name,default=None) :
		return getattr(self,name,default)

public_data = PublicData()

# print 'ProgramPath=',public_data.get('ProgramPath',None)
