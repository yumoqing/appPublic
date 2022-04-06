import sys
import logging
from functools import partial

levels={
	"debug":logging.DEBUG,
	"info":logging.INFO,
	"warning":logging.WARNING,
	"error":logging.error,
	"critical":logging.CRITICAL
}
defaultfmt = '%(asctime)s[%(name)s][%(levelname)s][%(filename)s:%(lineno)s]%(message)s'
logfile = -1
level = levels.get('info')

def create_logger(name, formater=defaultfmt, levelname='info', file=None):
	global logfile, level
	if logfile == -1:
		logfile = file
	ret = logging.getLogger(name)
	level = levels.get(levelname, levels.get('info'))
	ret.setLevel(level)
	format = logging.Formatter(formater)
	file_handler = None
	if logfile is not None:
		file_handler = logging.FileHandler(logfile)
	else:
		file_handler = logging.StreamHandler()
	
	file_handler.setFormatter(format)
	ret.addHandler(file_handler)
	return ret

class AppLogger:
	def __init__(self):
		self.logger = create_logger(self.__class__.__name__)
		self.debug = self.logger.debug
		self.info = self.logger.info
		self.warning = self.logger.warning
		self.error = self.logger.error
		self.critical = self.logger.critical
		self.exception = self.logger.exception
