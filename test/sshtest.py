import sys
import asyncio
from appPublic.sshx import SSHNode, SSHBash


if __name__ == '__main__':
	async def sysstdin_read():
		return os.read(sys.stdin.fileno(), 65535)

	async def sysstdout_write(x):
		sys.stdout.write(x.decode('utf-8'))

	async def test_sshbash():
		jp = {
			"host":"glib.cc",
			"username":"ceni",
			"port":10022
		}
		jn = SSHNode('atvoe.com', username="ymq", password="Ymq@651018")
		await jn.connect()
		bash = SSHBash(jn)
		print('tdryfguhijokpl')
		await bash.run(sysstdin_read, sysstdout_write)

	loop = asyncio.get_event_loop()
	loop.run_until_complete(test_sshbash())

