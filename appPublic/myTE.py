import os
import sys
import appPublic.myjson as json
from jinja2 import Environment,FileSystemLoader
import codecs
from appPublic.argsConvert import ArgsConvert
from appPublic.dictObject import DictObject
def isNone(obj):
	return obj is None


class MyTemplateEngine:
	def __init__(self,pathList,file_coding='utf-8',out_coding='utf-8'):
		self.file_coding = file_coding
		self.out_coding = out_coding
		loader = FileSystemLoader(pathList, encoding=self.file_coding)
		self.env = Environment(loader=loader)	
		denv={
			'json':json,
			'hasattr':hasattr,
			'int':int,
			'float':float,
			'str':str,
			'type':type,
			'isNone':isNone,
			'len':len,
			'recordFind':recordFind,
			'render':self.render,
			'renders':self.renders,
			'ArgsConvert':ArgsConvert,
			'renderJsonFile':self.renderJsonFile,
			'ospath':lambda x:os.path.sep.join(x.split(os.altsep)),
			'basename':lambda x:os.path.basename(x),
			'basenameWithoutExt':lambda x:os.path.splitext(os.path.basename(x))[0],
			'extname':lambda x:os.path.splitext(x)[-1],
		}
		self.env.globals.update(denv)

	def setGlobal(self,dic):
		self.env.globals.update(dic)
		
	def _render(self,template,data):
		self._setEnv()
		uRet = template.render(**data)
		return uRet.encode(self.out_coding)
		
	def renders(self,tmplstring,data):
		def getGlobal():
			return data
		self.set('global',getGlobal)
		template = self.env.from_string(tmplstring)
		return self._render(template,data)

	def render(self,tmplfile,data):
		def getGlobal():
			return data
		self.set('global',getGlobal)
		template = self.env.get_template(tmplfile)
		return self._render(template,data)

	def renderJsonFile(self,tmplfile,jsonfile):
		f = codecs.open(jsonfile,"r",self.file_coding)
		data = json.load(f)
		f.close()
		return self.render(tmplfile,data)
