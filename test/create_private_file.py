import sys
from appPublic.rsawrap import RSA

def gen(filename):
	rsa = RSA()
	pk = rsa.create_privatekey()
	rsa.write_privatekey(pk, filename)

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print('Usage\n%s private_file_name' % sys.argv[0])
		sys.exit(1)

	gen(sys.argv[1])
