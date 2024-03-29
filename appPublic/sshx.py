import os
import sys
import shlex
from functools import partial
from threading import Thread
from appPublic.myTE import tmpTml
import asyncio, asyncssh, sys

class SSHNode:
	def __init__(self, host, 
						username='root', 
						port=22, 
						password=None, 
						jumpers=[]):
		self.server2 = {
				"host":host,
				"username":username,
				"password":password,
				"port":port
		}
		self.jumpers = jumpers
		self.conn = None
		self.jumper_conns = []
		self.batch_cmds = []

	def info(self):
		d = {
			"jumpers":self.jumpers,
		}
		d.update(self.server2)
		return d

	def asjumper(self):
		a = self.jumpers.copy()
		a.append(self.server2)
		return a

	def set_jumpers(self, jumpers):
		self.jumpers = jumpers

	async def connect(self):
		refconn = None
		for j in self.jumpers:
			host = j['host']
			username = j.get('username', 'root')
			port = j.get('port',22)
			password=  j.get('password', None)
			if refconn:
				refconn = await refconn.connect_ssh(host,
									username=username,
									password=password,
									port=port)
			else:
				refconn = await asyncssh.connect(host,
									username=username,
									password=password,
									port=port)
			self.jumper_conns.append(refconn)

		host = self.server2['host']
		username = self.server2.get('username', 'root')
		port = self.server2.get('port',22)
		password = self.server2.get('password', None)
		if refconn:
			self.conn = await refconn.connect_ssh(host,
								username=username,
								port=port,
								password=password,
								known_hosts=None)
		else:
			self.conn = await asyncssh.connect(host,
								username=username,
								port=port)

	def close(self):
		self.conn.close()
		cnt = len(self.jumper_conns)
		cnt -= 1
		while cnt >= 0:
			self.jumper_conns[cnt].close()
			cnt -= 1
		self.jumper_conns = []
		self.conn = None

	async def _l2r(self, lf, rf):
		x = await asyncssh.scp(lf, (self.conn, rf), 
							preserve=True, recurse=True)
		return x

	async def _process(self, *args, **kw):
		a = await self.conn.create_process(*args, **kw)
		return a

	async def _r2l(self, rf, lf):
		x = await asyncssh.scp((self.conn, rf), lf,
							preserve=True, recurse=True)
		return x

	async def _cmd(self, cmd, input=None, stdin=None, stdout=None):
		return await self.conn.run(cmd, input=input, stdin=stdin, stdout=stdout)

	async def _xcmd(self, cmd, xmsgs=[], ns={}, 
						show_input=None,
						show_stdout=None):
		proc = await self._process(cmd, term_type='xterm',

										term_size=(80,24),
										encoding='utf-8'
		)
		buffer = ''
		
		msglen = len(xmsgs)
		for i in range(msglen):
			if xmsgs[i][0]:
				break
			s = xmsgs[i][1].format(**ns)
			proc.stdin.write(s)
		keyin = False
		def feed_data(xmsgs, debug_input):
			if len(xmsgs) == 0:
				return
			a = xmsgs[0]
			xmsgs.reverse()
			xmsgs.pop()
			xmsgs.reverse()
			s = a[1].format(**ns)
			proc.stdin.write(s)
			if debug_input:
				debug_input(f'{s=},{a=}')
			keyin = True

		already_output = False
		callee = None
		loop = asyncio.get_event_loop()
		while True:
			if proc.stdout.at_eof():
				break

			if keyin:
				keyin = False
				await proc.stdin.drain()

			if len(xmsgs) > 0 and already_output:
				f = partial(feed_data, xmsgs, show_input)
				callee = loop.call_later(xmsgs[0][0], f)
			x = await proc.stdout.read(1024)
			if callee:
				callee.cancel()
			if show_stdout:
				show_stdout(x)
			already_output = True

	async def _run(self, cmd, input=None, stdin=None, stdout=None):
		if cmd.startswith('l2r'):
			args = shlex.split(cmd)
			if len(args) == 3:
				x = await self._l2r(args[1], args[2]) 
				return x

		if cmd.startswith('r2l'):
			args = shlex.split(cmd)
			if len(args) == 3:
				x = await self._r2l(args[1], args[2]) 
				return x

		return await self._cmd(cmd, input=input, stdin=stdin, stdout=stdout)

	def show_result(self, x):
		if isinstance(x, Exception):
			print('Exception:',e)
		else:
			print('stdout:', x.stdout)
			print('stderr:', x.stderr)

	async def run(self, cmd, input=None, stdin=None, stdout=None):
		await self.connect()
		result = await self._run(cmd, input=input,
								stdin=stdin, stdout=stdout)
		self.close()
		return result

class SSHNodes:
	def __init__(self, nodes, usernmae='root', port=22, jumpers=[]):
		self.nodes = [ Node(n, username=username, port=port, jumpers=jumpers) for n in nodes ]
		self.batch_cmds = []

	def append_cmd(self, cmd, stdin=None, stdout=None):
		self.batch_cmds.append({
			"cmd":cmd,
			"stdin":stdin,
			"stdout":stdout})

	def show_result(self, result, i=0):
		if isinstance(result, Exception):
			print(f'Task {i} failed:{result}')
		elif result.exit_status != 0:
			print(f'Task {i} exit {result.exit_status}')
			print(result.stderr, end='')
		else:
			print(f'Task {i} successed:')
			print(result.stdout, end='')

	async def run(self, cmd, stdin=None, stdout=None):
		tasks = [ n.run(cmd, stdin=stdin, stdout=stdout) for n in self.nodes ]
		results = await asyncio.gather(*tasks, return_exceptions=True)
		return results

	async def exe_batch(self):
		tasks = [ n.exe_batch(self.batch_cmds) for n in self.nodes ]
		results = await asyncio.gather(*tasks, return_excetion=True)
		return results
		for i, result in enumerate(results):
			self.show_result(result,i)

async def main():
	if len(sys.argv) < 3:
		print(f'{sys.argv[0]} cmd host1 host2 ....')
		sys.exit(1)

	cmd = sys.argv[1]
	jumpor = {
		"host":"glib.cc",
		"username":"ceni",
		"port":10022
	}
	hosts = sys.argv[2:]
	mn = SSHNodes(hosts, jumpers=[jumpor])
	while True:
		print('input command:')
		cmd = input()
		print('input stdin:')
		stdin = input()
		if stdin == '':
			stdin = None
		print('input stdout:(default is stdout)')
		stdout = input()
		if stdout == '':
			stdout = None
		x = await mn.run(cmd, stdin=stdin, stdout=stdout)
		for r in x:
			if isinstance(r, Exception):
				print(r)
			else:
				print(r.stdout)

class SSHBash:
	def __init__(self, node, loop=None):
		if loop is None:
			loop = asyncio.get_event_loop()
		self.node = node
		self.loop = loop
		self.conn = None
		self.stdin_need = False
		self.subloop = asyncio.new_event_loop()
		self.subthread = Thread(target=self.start_thread_loop)
		self.subthread.setDaemon(True)
		self.subthread.start()

	def start_thread_loop(self):
		asyncio.set_event_loop(self.subloop)
		self.subloop.run_forever()
	
	def exit(self):
		if self.conn:
			self.node.close(self.conn)
		self.p_obj.close()
		self.subloop.stop()
		self.loop.stop()

	async def feed_stdin(self, f):
		self.stdin_need = False
		x = await f(65535)
		if x is None:
			self.exit()
		self.p_obj.stdin.write(x)
		await self.p_obj.stdin.drain()
		self.stdin_need = True

	async def run(self, read_co, write_co):
		await self.node.connect()
		self.p_obj = await self.node._process('bash', 
										term_type='vt100',
										term_size=(80,24),
										encoding=None)
		if isinstance(self.p_obj, Exception):
			print('Excetion:', self.p_obj)
			self.exit()
			return
		if self.p_obj is None:
			print('self.p_obj is None')
			self.exit()
			return
		# self.loop.add_reader(sys.stdin.fileno(), self.read_input)
		self.stdin_need = True
		while True:
			if self.stdin_need:
				asyncio.run_coroutine_threadsafe(self.feed_stdin(read_co), self.subloop)
				
			if self.p_obj.stdout.at_eof():
				self.exit()
				break
			x = await self.p_obj.stdout.read(1024)
			await write_co(x)
	
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
		jn = SSHNode('k3', jumpers=[jp])
		bash = SSHBash(jn)
		await bash.run(sysstdin_read, sysstdout_write)

	loop = asyncio.get_event_loop()
	loop.run_until_complete(test_sshbash())

