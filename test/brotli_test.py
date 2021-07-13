import sys
from brotli import compress, decompress

def do(fn):
	with open(fn, 'rb') as f:
		b = f.read()
		c = compress(b)
		d = decompress(c)
		print(fn,'\t',
			float(len(c))/float(len(b)))
fns = sys.argv[1:]
for fn in fns:
	do(fn)
