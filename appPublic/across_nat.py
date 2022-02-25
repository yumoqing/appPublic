
from natpmp import NATPMP as pmp
from aioupnp.upnp import UPnP
from requests import get
from .background import Background

class AcrossNat(object):
	def __init__(self):
		self.external_ip = None
		self.upnp = None
		self.pmp_supported = True
		self.upnp_supported = True
		self.init_pmp()

	async def init_upnp(self):
		if self.upnp is None:
			self.upnp = await UPnP.discover()

	def init_pmp(self):
		try:
			self.external_ip = pmp.get_public_address()
		except pmp.NATPMPUnsupportedError:
			self.pmp_supported = False

	def init_upnp(self):
		try:
			self.upnp = UPnP()
			devices = self.upnp.discover()
			if len(devices) == 0:
				self.upnp_supported = False
		except:
			self.upnp_supported = False

	async def get_external_ip(self):
		if self.pmp_supported:
			return self._pmp_get_external_ip()

		if self.upnp_supported:
			return await self.upnp.get_external_ip()

		try:
			return get('https://api.ipify.org').text
		except:
			return get('https://ipapi.co/ip/').text


	def _pmp_get_external_ip(self):
		return pmp.get_public_address()

	def _upnp_get_external_ip(self):
		
	await def upnp_map_port(inner_port, protocol='TCP', from_port=40003):
		protocol = protocol.upper()
		external_port = from_port
		while external_port < 52333:
			x = await self.upnp.get_specific_port_mapping(external_port, protocol)
			if len(x) == 0:
				break
			external_port += 1

		if external_port < 52333:
			await self.upnp.add_port_mapping(external_port,
									protocol,
									inner_port,
									lan_address,
									desc or 'user added')
			return external_port
		return None

	async def is_port_mapped(self, external_port, protocol='TCP'):
		protocol = protocol.upper()
		if self.upnp_supported:
			x = await self.upnp.get_specific_port_mapping(external_port, 
									protocol)
			if len(x) == 0:
				return True
			return False
		raise Exception('not implemented')

	async def port_unmap(self, external_port, protocol='TCP'):
		protocol = protocol.upper()
		if self.upnp_supported:
			await self.upnp.delete_port_mapping(external_port, protocol)
		raise Exception('not implemented')

	def map_port(self, inner_port, protocol='tcp', from_port=40003):
		if pmp_supported:
			return _map_port(inner_port, protocol=protocol)

		return self.upnp.add_port_mapping(
			
			inner_port, protocol=protocol)



pmp_supported = True

"""
_natmap mapping a localhost port to network gateway outter ip's port
input:
	port: integer, localhost host port
	protocal: string, 'tcp', or 'udp', default is 'tcp'
	from_port: integer, the return port will from this prot, 
				default is 49000, if mapping failed, increases by one, 
				and try it again. 

return:
	gateway outter ip's port, if gateway not support natpmp, return None
"""

def pmp_getExtenalIPAddress():
	return pmp.get_public_address()



def get_external_ip():
	global pmp_supported
	if pmp_supported:
		try:
			return pmp_get_public_address()
		except pmp.NATPMPUnsupportedError:
			pmp_supported = False
		except Exception as e:
			raise e
	upnp = UPnP()
	devices = upnp.discover()
	if len(devices) < 1:
		return None
	d = devices[0]
	services = d.get_services()

def _pmp_natmap(innerport, 
			protocol='tcp', 
			from_port=49000, 
			timeout=3600):
	gateway = pmp.get_gateway_addr()
	ret_port = from_port
	while 1:
		try:
			mode = pmp.NATPMP_PROTOCOL_TCP
			if protocol != 'tcp':
				mode = pmp.NATPMP_PROTOCOL_UDP

			x = pmp.map_port(mode, 
						ret_port, 
						innerport, 
						timeout, 
						gateway_ip=gateway)
			return x.public_port
		except pmp.NATPMPUnsupportedError:
			return None
		except Exception, e:
			time.sleep(0.01)
			ret_port+=1
			if ret_port > 60000:
				return None

def natmap(
