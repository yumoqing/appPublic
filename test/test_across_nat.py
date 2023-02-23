from appPublic.across_nat import *
import asyncio

async def run():
	an = AcrossNat()
	an.pmp_supported = False
	x = await an.get_external_ip()
	print('external ip=', x)
	print('pmp_supported=', an.pmp_supported,
			'upnp_supported=', an.upnp_supported)
	for p in [ 8080, 8081 ]:
		x = await an.map_port(p, 'TCP')
		print(p, '-->', x)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())

