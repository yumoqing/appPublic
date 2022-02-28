from appPublic.zmq_reqrep import ZmqReplier
import time

def handler(b):
	print(b.decode('utf-8'))
	return 'got it'

x = ZmqReplier('tcp://127.0.0.1:9999', handler)
x.run()
f = 0
while 1:
	time.sleep(0.1)
	if f==0:
		print(dir(x.sock.get_peer()))
	f += 1

x.stop()

