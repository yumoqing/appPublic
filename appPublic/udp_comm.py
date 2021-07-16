# -*- coding:UTF-8 -*-
from traceback import print_exc
from socket import *
import json
from appPublic.sockPackage import get_free_local_addr
from appPublic.background import Background
BUFSIZE = 1024 * 64
class UdpComm:
	def __init__(self, port, callback, timeout=1):
		self.callback = callback
		self.timeout = timeout
		self.host = get_free_local_addr()[0]
		self.port = port
		self.udpSerSock = socket(AF_INET, SOCK_DGRAM)
		# 设置阻塞
		self.udpSerSock.setblocking(1)
		# 设置超时时间 1s
		# self.udpSerSock.settimeout(timeout)
		self.udpSerSock.bind(('' ,port))
		self.run_flg = True
		self.thread = Background(self.run)
		self.thread.start()
	
	def run(self):
		while self.run_flg:
			try:
				b, addr = self.udpSerSock.recvfrom(BUFSIZE)
				if addr[0] != self.host:
					self.callback(b, addr)
			except Exception as e:
				print('exception happened:',e)
				print_exc()
				pass

	def stop(self):
		self.run_flg = False
		self.udpSerSock.close()
		
	def broadcast(self, data):
		broadcast_host = '.'.join(self.host.split('.')[:-1]) + '.255'
		udpCliSock = socket(AF_INET, SOCK_DGRAM)
		udpCliSock.settimeout(self.timeout)
		udpCliSock.bind(('', 0))  
		udpCliSock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  
		b = data
		if not isinstance(data, bytes):
			b = json.dumps(data).encode('utf-8')
		udpCliSock.sendto(b, (broadcast_host,self.port))
	
	def send(self,data,addr):
		b = data
		if not isinstance(data, bytes):
			b = json.dumps(data).encode('utf-8')
		if isinstance(addr,list):
			addr = tuple(addr)
		self.udpSerSock.sendto(b,addr)

	def sends(self,data, addrs):
		b = data
		if not isinstance(data, bytes):
			b = json.dumps(data).encode('utf-8')
		for addr in addrs:
			if isinstance(addr,list):
				addr = tuple(addr)
			self.udpSerSock.sendto(b,addr)

if __name__ == '__main__':
	import sys
	def msg_handle(data, addr):
		print('addr:', addr, 'data=', data)

	port = 50000
	if len(sys.argv)>1:
		port = int(sys.argv[1])
	d = UdpComm(port, msg_handle)
	x = input()
	while x:
		d.broadcast(x)
		x = input()

