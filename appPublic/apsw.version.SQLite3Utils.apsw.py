import os,sys
import thread
import apsw
import time
from localefunc import *
from folderUtils import mkdir
from PublicData import public_data
from mylog import mylog

def logit(s) :
	mylog('%s:%s' % (__file__,s))

class Record :
	def __init__(self,data,localize=False) :

		for i in data.keys() :
			d = data[i]
			if localize and type(d)==type('') :
				d = localeString(d)
			setattr(self,i.lower(),d)

	def __getattr__(self,name) :
		dict = self.__dict__
		name = name.lower()
		if name in dict.keys() :
			return dict[name]
		else :
			raise AttributeError(name)

	def __str__(self) :
		a = self.__dict__
		f = []
		for i in a.keys() :
			f.append("%s : %s" % (i,str(a[i])))
		return '[%s]' % '\n'.join(f)

def str2unicode(s) :
	if type(s) == type('') :
		try :
			ret = unicode(s,local_encoding)
			return ret
		except :
			try :
				ret = unicode(s,'utf8')
				return ret
			except :
				return buffer(s)
	return s

def unicode2str(s) :
	t = type(s)
	if t == type(5) :
		return long(s)
	if t == type(buffer('')) :
		return str(s)
	if t == type(u"w") :
		return s.encode('utf8')
	return s
	
def argConvert(args) :
	if args==None :
		return None
	t = type(args)
	if t==type(()) or t==type([]) :
		return [str2unicode(i) for i in args]
	if t==type({}) :
		for i in args.keys() :
			args[i] = str2unicode(args[i])
		return args
	return args
	
class SQLite3 :

	def __init__(self,dbpath,localize=False) :
		self.__dict__['threadMap'] = {}
		self.__dict__['localize'] = localize
		self.__dict__['dbpath'] = dbpath
		self.results = None
		self.con = None
		self.cursor = None
		self.sqlcmd = ''
		self._connection(dbpath)

	def _connection(self,dbpath=None) :
		if dbpath!=None :
			self.dbpath = dbpath
		self.con = apsw.Connection(self.dbpath)
		self.cursor = self.con.cursor()
		self.result = None
		self.sqlcmd = ''

	def __setattr__(self, name, value):
		id = thread.get_ident()
		if not self.__dict__['threadMap'].has_key(id):
			self.__dict__['threadMap'][id] = {}
		self.threadMap[id][name] = value

	def __getattr__(self, name):
		id = thread.get_ident()
		
		if not self.__dict__['threadMap'].has_key(id) :
			self.__dict__['threadMap'][id] = {}
		if self.__dict__['threadMap'][id].has_key(name) :
			return self.__dict__['threadMap'][id][name]
		raise AttributeError(name)

	def tables(self) :
		self.SQL("select * from sqlite_master where type='table'")
		r = self.FETCH()
		ts = []
		while r :
			ts.append(r.name)
			r = self.FETCH()
		return ts

	def columns(self,tablenmae) :
		self.SQL('select * from %s' % tablename)
		self.desc = self.results.getdescription()
		return desc

	def FETCHALL(self) :
		all=[]
		r = True
		while r:
			r = self.FETCH()
			if r :
				all.append(r)
		return all

	def _eatCursorNext(self) :
		if self.cursor==None :
			return None
		r = 1
		while r :
			try :
				r = self.cursor.next()
			except :
				return

	def SQL(self,cmd,args=(),retry=0) :
		if self.con==None :
			print("self.con==None")
			return -1		
		self._eatCursorNext()
		args = argConvert(args)
		self.lastSQL = cmd
		self.desc = None
		try :
			self.results = self.cursor.execute(cmd,args)
			return True
		except apsw.IncompleteExecutionError as e :
			r = True
			while r :
				r = self.FETCH()
			return self.SQL(cmd,args,retry + 1)
		except apsw.BusyError as e:
			if retry >20 :
				print("execute:(",cmd,")Busy, error",e)
				self.results=None
				raise e
			time.sleep(0.01)
			return self.SQL(cmd,args,retry + 1)
		except apsw.LockedError as e :
			if retry >20 :
				print("execute:(",cmd,")Locked, error",e)
				self.results = None
				raise e
			time.sleep(0.01)
			return self.SQL(cmd,args,retry + 1)
		except apsw.ThreadingViolationError as e :
			self._connection()
			return self.SQL(cmd,args,retry+1)
		except apsw.Error as e:
			print('execute:',cmd,'error',e)
			self.results = None
			raise 
		print("sql finish")
		return True
	
	def FETCH(self) :
		if self.results == None :
			print("FETCH error,results==None")
			return None
		if self.desc == None :
			try :
				self.desc = self.results.getdescription()
			except apsw.ExecutionCompleteError as e :
				# print("getdescription error",self.lastSQL,e)
				return None
			except Exception as e:
				print("fetch error",self.lastSQL,e)
				raise
		try :
			desc = self.desc
			d  = self.results.next()
			data = {}
			for i in range(len(d)) :
				data[desc[i][0]] = unicode2str(d[i])
			return Record(data,self.localize)
		except StopIteration :
			# print("StopIteration error")
			return None
		except apsw.Error as e:
			print("error happen",e,self,lastSQL)
			raise
		
	def COMMIT(self) :
		self.SQL('COMMIT')
			
	def ROLLBACK(self) :
		self.SQL('ROLLBACK')
 
	def BEGIN(self) :
		self.SQL('BEGIN')
		return
	
	def CLOSE(self) :
		self.con = None
		self.cursor = None


def getDataBase(name) :
	a_name='db_%s' % name
	db = public_data.get(a_name,None)
	if db==None :
		dbpath = public_data.get('dbpath_%s' % name,None)
		if dbpath==None :
			p = public_data.get('ProgramPath',None)
			if p==None:
				raise Exception('public_data must has a "ProgramPath" variable')
			p1 = os.path.join(p,'var')
			mkdir(p1)
			dbpath = os.path.join(p1,'%s.db3' % name)
			public_data.set('dbpath_%s' % name,dbpath)
		db = SQLite3(dbpath)
		public_data.set(a_name,db)
	try :
		con = db.con
	except :
		dbpath = public_data.get('dbpath_%s' % name,None)
		db._connection(dbpath)
	return db
