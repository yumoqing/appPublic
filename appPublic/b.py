from appPublic.zmqapi import run_proxy
import asyncio
import sys

if __name__ == '__main__':
    asyncio.run(run_proxy())

