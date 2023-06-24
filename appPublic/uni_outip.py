import time
from natpmp import NATPMP as pmp
import upnpclient
from ipgetter import IPgetter

def pmp_get_external_ip():
	return pmp.get_public_address()

def upnp_get_external_ip():
	igd = upnpclient.discover()[0]
	s_names = [ n for n in igd.service_map.keys() if 'WAN' in n and 'Conn' in n]
	upnp = igd.service_map[s_names[0]]
	x = upnp.GetExternalIPAddress()
	return x.get('NewExternalIPAddress', None)
	
def ipgetter_get_external_ip():
	getter = IPgetter()
	ip = None
	while ip is None:
		ip = getter.get_external_ip()
		if ip:
			return ip
		time.sleep(0.5)

def get_external_ip():
	ip = pmp_get_external_ip()
	if ip:
		return ip
	ip = upnp_get_external_ip()
	if ip:
		return ip
	return ipgetter_get_external_ip()

def run():
	while True:
		ip = get_external_ip()
		if ip:
			print(ip)
		time.sleep(10)


