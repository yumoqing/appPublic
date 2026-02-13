
import asyncio
from collections.abc import Coroutine

import zmq
import zmq.asyncio
import json
from .worker import awaitify

from zmq.asyncio import Context
from zmq.utils.monitor import parse_monitor_message
from appPublic.jsonConfig import getConfig

async def run_proxy():
	config = getConfig()
	subscribe_url = config.subscribe_url or 'tcp://127.0.0.1:5556'
	publish_url = config.publish_url or 'tcp://127.0.0.1:5555'
    ctx = zmq.asyncio.Context()

    # 1. 面对 Publisher 的前端 (XSUB)
    frontend = ctx.socket(zmq.XSUB)
    frontend.bind(publish_url)  # 发布者往这里 connect

    # 2. 面对 Subscriber 的后端 (XPUB)
    backend = ctx.socket(zmq.XPUB)
    backend.bind(subscribe_url)   # 订阅者往这里 connect

    print("【Proxy】启动：Pub 连 5555，Sub 连 5556")

    # 核心：启动内置代理，它会自动把 frontend 接收的消息广播给 backend
    # 并且把 backend 的订阅信息同步给 frontend
    try:
        await awaitify(zmq.proxy)(frontend, backend)
    except Exception as e:
        print(f"Proxy 异常退出: {e}")
    finally:
        frontend.close()
        backend.close()
        ctx.term()

async def zmq_subcribe(special_key: str, callback=None):
	config = getConfig()
	subscribe_url = config.subscribe_url or 'tcp://127.0.0.1:5556'
	ctx = Context()
	sock = ctx.socket(zmq.SUB)
	sock.connect(subscribe_url)

	# 设置过滤：只接收以 special_key 开头的消息
	sock.setsockopt_string(zmq.SUBSCRIBE, special_key)
	
	print(f"【服务端】启动，仅等待 Key 为 '{special_key}' 的消息...")

	content = ''
	try:
		while True:
			# 接收消息（multipart 格式，第一部分是 key，第二部分是内容）
			msg = await sock.recv_multipart()
			key = msg[0].decode()
			content = msg[1].decode()
			# print(f"【服务端】匹配成功！Key: {key}, 内容: {content}")
			if callback is None:
				break
			await callback(content)
	except asyncio.CancelledError:
		pass
	finally:
		sock.close()
		ctx.term()
	return content

async def zmq_publish(key, content):
	config = getConfig()
	publish_url = config.publish_url or 'tcp://127.0.0.1:5555'
	ctx = Context()
	sock = ctx.socket(zmq.PUB)
	sock.setsockopt(zmq.LINGER, 1000)
	sock.connect(publish_url)
	await asyncio.sleep(0.1)
	await sock.send_multipart([key.encode(), content.encode()])
	print(f"【PUB】消息已发送: {key}")
	await asyncio.sleep(0.1)
	sock.close()
	ctx.term()

class Publisher:
	def __init__(self,port,coding='utf-8',msgid=1000):
		self.port = port
		self.socket = None
		self.coding = coding
		self.msgid = msgid
		context = zmq.asyncio.Context()
		self.socket = context.socket(zmq.PUB)
		self.socket.bind('tcp://*:%d' % self.port)

	async def publish(self,msg,msgtype='text',msgid=-1):
		print(msg,msgtype)
		if msgid == -1:
			msgid = self.msgid
		if msgtype != 'text':
			msg = json.dumps(msg)
			msgtype = 'json'
		s = '%d %s %s' % (msgid,msgtype,msg)
		print(s,msgtype,msgid)
		b = s.encode(self.coding)
		await self.socket.send(b)

	def __del__(self):
		self.socket.close()

class Subscriber:
	def __init__(self,host,ports,msgid,coding='utf-8'):
		self.host = host
		self.ports = ports
		self.msgid = msgid
		self.coding = coding
		context = zmq.asyncio.Context()  
		self.socket = context.socket(zmq.SUB)  
		f = b'%d' % self.msgid
		self.socket.setsockopt(zmq.SUBSCRIBE, f)  
		for p in self.ports:
			self.socket.connect("tcp://%s:%d" % (self.host,p))
	
	def addPort(self,port):
		self.socket.connect("tcp://%s:%d" % (self.host,port))
		#f = b'%d' % self.msgid
		#self.socket.setsockopt(zmq.SUBSCRIBE, f)  
		
	async def subscribe(self):
		ret = await self.socket.recv()
		ret = ret.decode(self.coding)
		msgid, msgtype, body = ret.split(' ',2)
		print('msgid=',msgid,'msgtype=',msgtype,'body=',body)
		if msgtype == 'json':
			return json.loads(body)
		return body

	def __del__(self):
		self.socket.close()

class RRServer:
	"""
	a request / response mode server
	"""
	def __init__(self,port,handler=None):
		self.port = port
		self.handler = handler
		print(type(self.handler))
		
	async def run(self):
		running = True
		context = zmq.asyncio.Context()
		socket = context.socket(zmq.REP)
		socket.bind('tcp://*:%s' % self.port)
		while running:
			rmsg = await socket.recv()
			wmsg = rmsg
			if self.handler is not None:
				wmsg = self.handler(rmsg)
				if isinstance(wmsg,Coroutine):
					wmsg = await wmsg
			await socket.send(wmsg)
		socket.close()

class RRClient:
	"""
	a request / response mode client
	"""
	def __init__(self,host,port):
		self.host = host
		self.port = port
		context = zmq.asyncio.Context()
		self.socket = context.socket(zmq.REQ)
		self.socket.connect('tcp://%s:%d' % (self.host,self.port))
	
	async def request(self,msg):
		await self.socket.send(msg)
		return await self.socket.recv()


class PPPusher:
	"""
	pusher of Push / Pull mode
	"""
	def __init__(self,host,port):
		self.host = host
		self.port = port
		context = zmq.asyncio.Context()
		self.socket = context.socket(zmq.PUSH)
		self.socket.bind('tcp://%s:%d' % (self.host,self.port))

	async def push(self,msg):
		await self.socket.send(msg)

class PPPuller:
	"""
	puller of Push / Pull mode
	"""
	def __init__(self,host,port,handler=None):
		self.host = host
		self.port = port
		self.handler = handler
		
	async def run(self):
		self.running = True
		context = zmq.asyncio.Context()
		socket = context.socket(zmq.PULL)
		socket.bind('tcp://%s:%d' % (self.host,self.port))
		while self.running:
			msg = await self.socket.recv()
			if self.handler is not None:
				x = self.handler(msg)
				if isinstance(x,Coroutine):
					await x

class PairClient:
	"""
	client of Pair mode 
	"""
	def __init__(self,host,port):
		self.host = host
		self.port = port
		context = zmq.asyncio.Context()
		self.socket = context.socket(zmq.PAIR)
		self.socket.bind('tcp://%s:%d' % (self.host,self.port))

	async def request(self,msg):
		await self.socket.send(msg)
		return await self.socket.recv()

class PairServer:
	"""
	server of Pair mode
	"""
	def __init__(self,port,handler=None):
		self.port = port
		self.handler = handler
		self.running = True

	async def run(self):
		self.running = True
		context = zmq.asyncio.Context()
		socket = context.socket(zmq.PAIR)
		socket.bind('tcp://*:%d' % self.port)
		while self.running:
			msg = await socket.recv()
			ret = msg
			if self.handler is not None:
				ret = self.handler()
				if isinstance(ret,Coroutine):
					ret = await ret
			await socket.send(ret)

if __name__ == '__main__':
	asyncio.run(run_proxy())
