import sys
import os
import requests

from appPublic.httpclient import JsonHttpAPI

def main():
	headers={
		"Content-Type": "application/json"
	}

	data = """{
		"messages":[
			{
				"role":"system",
				"content":"你是一个面向对象的python和js全栈式高级程序员"
			},
			{
				"role":"user",
				"content":"编写一个完整的云管理系统，客户前端，管理前端以及后台， 后台用python实现，前台用js实现"
			}
		],
		"model":"devstral"
	}"""

	url = "http://devops.opencomputing.ai/v1/chat/completions"
	x = requests.post(url, 
                     headers=headers,
                     data=data)
	print(x.json())

if __name__ == '__main__':
	main()

