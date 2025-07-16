import sys
from brotli import compress, decompress
import zlib

def do(fn):
	with open(fn, 'rb') as f:
		b = f.read()
		c = compress(b)
		zc = zlib.compress(b)
		print(fn,'\t',
			float(len(c))/float(len(b)), float(len(zc))/float(len(b)))
fns = sys.argv[1:]
for fn in fns:
	do(fn)
