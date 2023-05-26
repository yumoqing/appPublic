import re
import time
import requests

class IpGetter:
	def __init__(self, url, parser):
		self.url = url
		self.parser = parser
		self.cnt = 0
		self.total_time = 0
		self.avg_time = 0
	
	def get(self):
		tim1 = time.time()
		r = requests.get(self.url)
		txt = r.text
		ip = self.parser(txt)
		tim2 = time.time()
		self.cnt += 1
		self.total_time += tim2 - tim1
		self.avg_time = self.total_time / self.cnt
		return ip

	def get_average_time(self):
		return self.avg_time

class OutIP:
	def __init__(self):
		self.getters = []
		self.set_known_getters()
	
	def set_known_getters(self):
		g = IpGetter('http://ipinfo.io/ip', lambda x: x)
		self.add_getter(g)
		g = IpGetter('https://api.ipify.org', lambda x: x)
		self.add_getter(g)
		def f(t):
			return re.compile(r'Address: (\d+.\d+.\d+.\d+)').search(t).group(1)
		g = IpGetter('http://checkip.dyndns.com', f)
		self.add_getter(g)
	
	def add_getter(self, getter):
		self.getters.append(getter)
	
	def get(self):
		gs = self.getters.copy()
		gs.sort(key=lambda a: a.get_average_time())
		g = gs[0]
		return g.get()

if __name__ == '__main__':
	oi = OutIP()
	i = 0
	while i < 100:
		ip = oi.get()
		print('ip = ', ip)
		time.sleep(1)
		i += 1
	
