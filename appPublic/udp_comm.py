# -*- coding:UTF-8 -*-
from socket import *
import json
from appPublic.sockPackage import get_free_local_addr
from appPublic.background import Background
BUFSIZE = 1024
class UdpComm:
	def __init__(self, port, callback, timeout=1):
		self.callback = callback
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
				data = json.loads(b)
				if addr[0] != self.host:
					self.callback(data, addr)
				# ret = json.dumps(self.info).encode('utf-8')
				# self.udpSerSock.sendto(ret, addr)
			except Exception as e:
				print('exception happened:',e)
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
		b = json.dumps(data).encode('utf-8')
		udpCliSock.sendto(b, (broadcast_host,self.port))

	def send(self,data,addr):
		b = json.dumps(data).encode('utf-8')
		self.udpSerSock.sendto(b,addr)

	def sends(self,data, addrs):
		b = json.dumps(data).encode('utf-8')
		for addr in addrs:
			self.udpSerSock.sendto(b,addr)
