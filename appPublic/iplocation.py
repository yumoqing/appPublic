import os
import sys
from requests import get
from bs4 import BeautifulSoup
from appPublic.http_client import Http_Client
from appPublic.sockPackage import get_free_local_addr
public_headers = {
	"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36"
}

def get_outip():
	ip = get('https://api.ipify.org').content.decode('utf8')
	return ip

def ipip(ip=None):
	# ipip.net
	if ip is None:
		ip = get_outip()
	api= f"http://freeapi.ipip.net/{ip}"
	hc = Http_Client()
	r= hc.get(api, headers=public_headers)
	return {
		'country':r[0],
		'city':r[2]
	}

def iplocation(ip=None):
	if ip is None:
		ip = get_outip()
	# apikey come from
	# https://app.apiary.io/globaliptv/tests/runs
	# using my github accout
	apikey='c675f89c4a0e9315437a1a5edca9b92c'
	api = f"https://www.iplocate.io/api/lookup/{ip}?apikey={apikey}",
	hc = Http_Client()
	r= hc.get(api, headers=public_headers)
	return r

def ipaddress_com(ip=None):
	if ip is None:
		ip = get_outip()
	url = f'https://www.ipaddress.com/ipv4/{ip}'
	print('ipaddress_com(),url=', url)
	hc = Http_Client()
	r = hc.get(url, headers=public_headers)
	bs = BeautifulSoup(r, 'html.parser')
	section = bs.find_all('section')[0]
	trs = section.find_all('tr')
	d = {}
	for tr in trs:
		th = tr.find_all('th')[0]
		td = tr.find_all('td')[0]
		# print(th.contents, td.contents)
		if th.contents[0] == 'IP Latitude':
			d['lat'] = float(td.contents[0].split(' ')[0])
			continue
		if th.contents[0] == 'IP Country':
			# print('ip country:contents[-1]=', td.contents[-1])
			x = td.contents[-1].split('(')[0].strip()
			while x[0] <= ' ' or x[0] >= chr(128):
				x = x[1:]
			d['country'] = x
			continue
		if th.contents[0] == 'IP Longitude':
			d['lon'] = float(td.contents[0].split(' ')[0])
			continue
		if th.contents[0] == 'IP City':
			d['City'] = td.contents[0]
			
	return d

def get_ip_location(ip):
	apis = {
		"ipaddress":ipaddress_com,
		"ipip.net":ipip,
		"iplocation":iplocation,
	}
	hc = Http_Client()
	for k,v in apis.items():
		try:
			r = v(ip)
			return r
		except:
			pass
		
if __name__ == '__main__':
	print(get_free_local_addr())
	if len(sys.argv) > 1:
		info = get_ip_location(sys.argv[1])
		print(info)

