from appPublic.zmqapi import zmq_subscribe
import asyncio
import sys

async def show_message(msg):
    print(f'message received:{msg}')

async def main():
    await zmq_subscribe(sys.argv[1], callback=show_message)

if __name__ == '__main__':
    asyncio.run(main())

