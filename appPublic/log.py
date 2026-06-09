import os
import sys
import codecs
import threading
import queue
from traceback import format_exc
from appPublic.timeUtils import timestampstr
from appPublic.Singleton import SingletonDecorator
import inspect

def my_function():
    frame_info = inspect.currentframe()
    caller_frame = frame_info.f_back
    file_name = inspect.getframeinfo(caller_frame).filename
    line_number = inspect.getframeinfo(caller_frame).lineno


@SingletonDecorator
class MyLogger:
	levels={
		"clientinfo":7,
		"info":6,
		"debug":5,
		"warning":4,
		"error":3,
		"exception":2,
		"critical":1
	}
	formater='%(timestamp)s[%(name)s][%(levelname)s][%(filename)s:%(lineno)s]%(message)s\n'
	def __init__(self, name, levelname='debug', logfile=None):
		self.name = name
		self.levelname = levelname
		self.level = self.levels.get(levelname)
		self.logfile = logfile
		self.logger = None
		# Async write queue + background thread
		self._q = queue.Queue(maxsize=10000)
		self._worker = threading.Thread(target=self._write_loop, daemon=True)
		self._worker.start()

	def _get_logger(self):
		"""Lazy open file handle, keep it open."""
		if self.logger is not None:
			return self.logger
		if self.logfile:
			self.logger = codecs.open(self.logfile, 'a', 'utf-8')
		else:
			self.logger = sys.stdout
		return self.logger

	def _write_loop(self):
		"""Background thread: drain queue and write to file."""
		fh = None
		while True:
			try:
				item = self._q.get(timeout=1.0)
				if item is None:
					# Poison pill: shut down
					if fh is not None:
						try:
							fh.flush()
							if fh is not sys.stdout:
								fh.close()
						except Exception:
							pass
					break
				# Detect log rotation: if file was moved/renamed, reopen
				if fh is not None and self.logfile and not os.path.exists(self.logfile):
					try:
						fh.flush()
						fh.close()
					except Exception:
						pass
					fh = None
					self.logger = None
				if fh is None:
					fh = self._get_logger()
				item = item[:4096]
				fh.write(item)
				fh.flush()
				# Only flush on critical/exception to avoid blocking on slow disks
				#if item.find('[exception]') >= 0 or item.find('[critical]') >= 0:
				#	fh.flush()
			except queue.Empty:
				# Periodic flush to prevent data loss on crash
				if fh is not None:
					try:
						fh.flush()
					except Exception:
						pass
			except Exception:
				pass

	def log(self, levelname, message, frame_info):
		caller_frame = frame_info.f_back
		filename = inspect.getframeinfo(caller_frame).filename
		lineno = inspect.getframeinfo(caller_frame).lineno
		level = self.levels.get(levelname)
		if level > self.level:
			return
		data = {
			'timestamp': timestampstr(),
			'name': self.name,
			'levelname': levelname,
			'message': message,
			'filename': filename,
			'lineno': lineno
		}
		s = self.formater % data
		try:
			self._q.put_nowait(s)
		except queue.Full:
			# Queue full: drop oldest (non-blocking, never stall the event loop)
			try:
				self._q.get_nowait()
				self._q.put_nowait(s)
			except Exception:
				pass
	
def debug_params(name, d, maxlen=100):
    """Compact debug output: show all keys but truncate long values."""
    if not isinstance(d, dict):
        debug(f'{name}: {d}')
        return
    summary = {}
    for k, v in d.items():
        s = str(v)
        if len(s) > maxlen:
            summary[k] = s[:maxlen] + f'...({len(s)}ch)'
        elif isinstance(v, list) and len(v) > 3:
            summary[k] = f'[{len(v)} items]'
        else:
            summary[k] = v
    debug(f'{name}: {summary}')



def clientinfo(message):
	frame_info = inspect.currentframe()
	logger = MyLogger('Test')
	logger.log('clientinfo', message, frame_info)

def info(message):
	frame_info = inspect.currentframe()
	logger = MyLogger('Test')
	logger.log('info', message, frame_info)

def debug(message):
	frame_info = inspect.currentframe()
	logger = MyLogger('Test')
	logger.log('debug', message, frame_info)

def warning(message):
	frame_info = inspect.currentframe()
	logger = MyLogger('Test')
	logger.log('warning', message, frame_info)

def error(message):
	frame_info = inspect.currentframe()
	logger = MyLogger('Test')
	logger.log('error', message, frame_info)

def critical(message):
	frame_info = inspect.currentframe()
	logger = MyLogger('Test')
	logger.log('critical', message, frame_info)

def exception(message):
	frame_info = inspect.currentframe()
	tb_msg = format_exc()
	msg = f'{message}\n{tb_msg}'
	logger = MyLogger('exception')
	logger.log('exception', msg, frame_info)
