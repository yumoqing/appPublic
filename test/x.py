import asyncio
import asyncssh
import sys
import termios
import tty
import fcntl
import struct
import signal


class SSHInteractiveClient:
    def __init__(self, host, username, password=None, port=22, known_hosts=None):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.known_hosts = known_hosts
        self._old_term_attrs = None
        self._process = None

    def _get_terminal_size(self):
        try:
            h, w, _, _ = struct.unpack(
                'HHHH',
                fcntl.ioctl(sys.stdin, termios.TIOCGWINSZ,
                            struct.pack('HHHH', 0, 0, 0, 0))
            )
            return h, w
        except Exception:
            return 24, 80

    def _resize_handler(self, signum, frame):
        if self._process:
            rows, cols = self._get_terminal_size()
            self._process.set_terminal_size(rows, cols)

    async def _handle_stdin(self):
        try:
            while True:
                ch = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.read, 1)
                if ch:
                    self._process.stdin.write(ch)
        except asyncio.CancelledError:
            pass

    def _enable_raw_mode(self):
        self._old_term_attrs = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

    def _restore_terminal(self):
        if self._old_term_attrs:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_term_attrs)

    async def connect_and_run(self):
        self._enable_raw_mode()
        rows, cols = self._get_terminal_size()

        async with asyncssh.connect(
            self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            known_hosts=self.known_hosts
        ) as conn:
            self._process = await conn.create_process(term_type='xterm', term_size=(rows, cols))
            signal.signal(signal.SIGWINCH, self._resize_handler)

            stdin_task = asyncio.create_task(self._handle_stdin())

            try:
                async for line in self._process.stdout:
                    print(line, end='', flush=True)
            except (asyncio.CancelledError, EOFError):
                pass
            finally:
                stdin_task.cancel()
                self._restore_terminal()


# 示例使用方法
if __name__ == '__main__':
    client = SSHInteractiveClient(
        host='180.76.111.84',
        username='root',
        password='Kyy@123456',  # 或设为 None，使用 key 登录
        known_hosts=None  # 不验证 known_hosts
    )

    try:
        asyncio.run(client.connect_and_run())
    except (asyncssh.Error, OSError) as e:
        print(f'Connection failed: {e}')
    except KeyboardInterrupt:
        client._restore_terminal()

