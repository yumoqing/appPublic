import sys
import os
import asyncio

from appPublic.httpclient import JsonHttpAPI

async def main():
	headers="""{
		"Content-Type": "application/json"
	}"""

	data = """{"model": "devstral", "stream":true, "messages": [{"role": "user", "content": "who are you"}], "stream": true}"""

	jha = JsonHttpAPI()
	url = "https://www.baidu.com"
	url = "https://sage.opencomputing.ai"
	async for d in jha(url):
		print(d)
		print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')

if __name__ == '__main__':
	asyncio.get_event_loop().run_until_complete(main())

