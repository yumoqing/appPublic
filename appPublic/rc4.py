# -*- coding: utf-8 -*-  
import random, base64  
from hashlib import sha1  
 
class RC4:
	def __init__(self,data_coding='utf8'):
		self.bcoding = 'iso-8859-1'
		self.dcoding = data_coding
		self.salt = b'AFUqx9WZuI32lnHk'
	
	def _crypt(self,data,key):
		"""RC4 algorithm return bytes"""
		x = 0  
		box = [i for i in range(256) ]
		for i in range(256):  
			x = (x + box[i] + key[i % len(key)]) % 256  
			box[i], box[x] = box[x], box[i]  
		x = y = 0  
		out = []  
		for char in data:
			x = (x + 1) % 256  
			y = (y + box[x]) % 256  
			box[x], box[y] = box[y], box[x]  
			out.append(chr(char ^ box[(box[x] + box[y]) % 256]))  

		return ''.join(out).encode(self.bcoding) 
  
	def encode_bytes(self, bdata, key):
		a = sha1(key + self.salt)
		k = a.digest()
		data = self.salt + self._crypt(bdata, k)
		return data

	def encode(self,data, key,encode=base64.b64encode, salt_length=16):  
		"""RC4 encryption with random salt and final encoding"""  
		if type(data)==type(''):
			data = data.encode(self.dcoding)
		key = key.encode(self.bcoding)
		self.encode_bytes(data, key)
		if encode:  
			data = encode(data)
		return data.decode(self.dcoding)

	def decode_bytes(self, data, key):
		salt_length = 16
		salt = data[:salt_length]
		a = sha1(key + self.salt)
		k = a.digest() #.decode('iso-8859-1')
		r = self._crypt(data[salt_length:], k)
		return r

	def decode(self,data, key,decode=base64.b64decode, salt_length=16):  
		"""RC4 decryption of encoded data"""  
		if type(data)==type(''):
			data = data.encode(self.dcoding)
		key = key.encode(self.bcoding)
		if decode:  
			data = decode(data)  
		r = self.decode_bytes(data, key)
		return r.decode(self.dcoding)

  
if __name__=='__main__':  
	# 需要加密的数据长度没有限制 
	# 密钥 
	data=b"231r3 feregrenerjk gkht324g8924gnfw k;ejkvwkjerv"
	key = b'123456'  
	rc4 = RC4()
	print(data)
	# 加码  
	encoded_data = rc4.encode_bytes(data,key)  
	print(encoded_data,len(encoded_data) )
	# 解码  
	decoded_data = rc4.decode_bytes(encoded_data,key)  
	print(data, decoded_data, decoded_data==data)
