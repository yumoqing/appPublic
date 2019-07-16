from twisted.enterprise.adbapi import ConnectionPool,Transaction

#import pymssql
#import ibm_db
#import cx_Oracle

def dbPool(dbdef):
	pool = ConnectionPool(dbdef.driver,**dbdef.kwargs)
	return pool
	
def dbConnect(pool):
	conn = pool.connect()
	#conn.as_dict = True
	return conn

def dbClose(pool,conn):
	pool.disconnect(conn)
	
def dbCursor(pool,conn):
	return Transaction(pool,conn)

if __name__ == '__main__':
	from appPublic.dictObject import DictObject
	dbdict= {
		"driver":"pymssql",
		"kwargs":{
			"cp_max":30,
			"cp_min":10,
			"host":"localhost",
			"user":"sa",
			"password":"ymq123",
			"database":"dzh"
		}
	}
	dbdef = DictObject(**dbdict)
	pool = dbPool(dbdef)
	conn =  dbConnect(pool)
	cur = dbCursor(pool,conn)

	for i in range(20):
		r = cur.execute("insert into dbo.TQ_QT_INDEX (ID,TRADEDATE,SECODE,TMSTAMP) values(%d,'%s','0','11:22')" % (i,"2015-12-31"))
	cur.close()
	conn.commit()
	dbClose(pool,conn)
	pool.close()