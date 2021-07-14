
from appPublic.rsa import RSA
from appPublic.dataencoder import DataEncoder

Nodes = {
}

def get_pubkey(id):
	node = Nodes.get(id)
	return node.public_key


Nodes['node1'] = node1 = DataEncoder('node1', get_pubkey, 'prikey1.rsa')
Nodes['node2'] = node2 = DataEncoder('node2', get_pubkey, 'prikey2.rsa')

node1.set_peer_pubkey('node2', get_pubkey('node2'))
node2.set_peer_pubkey('node1', get_pubkey('node1'))

data1 = {
	'a':'iy34ti3y42ti23t425g4',
	'b':100,
	'c':'100',
	'd':[1124,'34t342',5445]
}
d = node1.pack('node2', data1)

try:
	data2 = node2.unpack('node1', d)
	print(data1,'<===>', data2)
except:
	print('ERROR:')

print('check c', node1.pack_d[0] == node2.unpack_d[0]) 
print('check d', node1.pack_d[1] == node2.unpack_d[1]) 
print('check k', node1.pack_d[2] == node2.unpack_d[2], len(node1.pack_d[2])) 
print('check s', node1.pack_d[3] == node2.unpack_d[3], len(node1.pack_d[3])) 
