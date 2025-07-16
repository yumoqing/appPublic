
import asyncio
from aioupnp.upnp import UPnP

async def main():
	upnp = await UPnP.discover()
	print(dir(upnp))
	print('gateway=', upnp.gateway, upnp.gateway_address, upnp.lan_address)
	print(await upnp.get_external_ip())
	port = 40009
	while port < 41000:
		x = await upnp.get_specific_port_mapping(40009, 'TCP')
		if len(x) == 0:
			print(port, 'port available')
			break
		else:
			print(port, 'port occupied')
		port += 1

	print("adding a port mapping")

	x = await upnp.add_port_mapping(port, 'TCP', 8999, '192.168.1.8', 'test mapping')
	print(8999, '-->', port)
	print('x=', x, await upnp.get_redirects())

	# print("deleting the port mapping")
	# await upnp.delete_port_mapping(51234, 'TCP')
	# print(await upnp.get_redirects())


asyncio.run(main())
