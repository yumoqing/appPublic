import asyncio
from appPublic.worker import awaitify

async def t():
	pass

def main(x,y, a=0, b=0):
	print(f'{x=},{y=},{a=},{b=}')

if __name__ == '__main__':
	f = awaitify(main)
	loop = asyncio.new_event_loop()
	loop.run_until_complete(f(5,6,b=5))

