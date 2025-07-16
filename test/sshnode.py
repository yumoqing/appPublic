import asyncio
import asyncssh
import sys
import termios
import tty
import signal
from appPublic.sshx import SSHServer

class InteractiveSSHClient(asyncssh.SSHClientSession):
	def __init__(self):
		self._chan = None
		self._stdin_task = None

	def connection_made(self, chan):
		self._chan = chan
		self._stdin_task = asyncio.create_task(self._forward_stdin())

	async def _forward_stdin(self):
		old_attrs = termios.tcgetattr(sys.stdin)
		try:
			tty.setraw(sys.stdin.fileno())
			while True:
				data = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.read, 1)
				if not data:
					break
				self._chan.write(data)
		except asyncio.CancelledError:
			pass
		finally:
			termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_attrs)

	def data_received(self, data, datatype):
		print(data, end='', flush=True)

	def connection_lost(self, exc):
		if self._stdin_task:
			self._stdin_task.cancel()

def get_terminal_size():
	try:
		import fcntl, struct
		h, w, hp, wp = struct.unpack('HHHH',
			fcntl.ioctl(sys.stdin, termios.TIOCGWINSZ,
						struct.pack('HHHH', 0, 0, 0, 0)))
		return (h, w)
	except:
		return (24, 80)  # fallback


async def run_interactive_bash():
	term_size = get_terminal_size()

	node = {
		"host":"192.168.16.8",
		"username":"root",
		"password":"Kyy@123456",
		"jumpservers" : [
			{
				"host":"git.opencomputing.cn",
				"username":"ymq",
				"password":"Ymq@651018"
			}
		]
	}
	jumpservers = [
		{
			"host":"git.opencomputing.cn",
			"username":"ymq",
			"password":"Ymq@651018"
		}
	]
	node = SSHServer(node)
	async with node.get_connector() as conn:
		A, B = await conn.create_session(
			InteractiveSSHClient,
			term_type='xterm',
			term_size=term_size
		)
		print(f'{A=}, {B=}')
		# 监听窗口 resize 信号，更新远端窗口大小
		def resize_handler(signum, frame):
			nonlocal A
			if A:
				rows, cols = get_terminal_size()
				chan.change_pty('xterm', term_size=(rows, cols))

		signal.signal(signal.SIGWINCH, resize_handler)

		await A.wait_closed()

if __name__ == '__main__':
	try:
		asyncio.run(run_interactive_bash())
	except (OSError, asyncssh.Error) as e:
		print(f'SSH session failed: {e}')
	except KeyboardInterrupt:
		pass

