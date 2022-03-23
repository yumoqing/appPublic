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
defaultfmt = '%(asctime)s[%(name)s][%(filename)s:%(lineno)s]%(message)s'

def create_logger(name, formater=defaultfmt, levelname='info', file=None):
	ret = logging.getLogger(name)
	level = levels.get(levelname, levels.get('debug'))
	ret.setLevel(level)
	format = logging.Formatter(formater)
	file_handler = None
	if file is not None:
		file_handler = logging.FileHandler(file)
	else:
		file_handler = logging.StreamHandler()
	
	file_handler.setFormatter(format)
	ret.addHandler(file_handler)
	return ret
