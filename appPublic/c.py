import asyncio
import sys
from appPublic.zmqapi import zmq_publish

async def main():
    await zmq_publish(sys.argv[1], sys.argv[2])

if __name__ == '__main__':
    asyncio.run(main())

