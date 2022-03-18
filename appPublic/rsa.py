from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import base64

class RSA:
	def __init__(self):
		pass
	
	def write_privatekey(self,private_key,fname,password=None):
		pwd = password
		pem = ''
		if pwd is not None:
			pwd = bytes(pwd,encoding='utf8')  if not isinstance(pwd, bytes) else pwd
			pem = private_key.private_bytes(
				encoding=serialization.Encoding.PEM,
				format=serialization.PrivateFormat.PKCS8,
				encryption_algorithm=serialization.BestAvailableEncryption(pwd)
			)
		else:
			pem = private_key.private_bytes(
				encoding=serialization.Encoding.PEM,
				format=serialization.PrivateFormat.TraditionalOpenSSL,
				encryption_algorithm=serialization.NoEncryption()
			)
		

		with open(fname,'w') as f:
			text = pem.decode('utf8')
			f.write(text)

	def publickeyText(self,public_key):
		pem = public_key.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
		)
		text = pem.decode('utf8')
		return text
		
	def write_publickey(self,public_key,fname):
		text = self.publickeyText(public_key)
		with open(fname,'w') as f:
			f.write(text)
		
	def read_privatekey(self,fname,password=None):
		pwd = password
		if password is not None:
			pwd = bytes(password,encoding='utf8')  if not isinstance(password, bytes) else password
		with open(fname, "rb") as key_file:
			key = serialization.load_pem_private_key(
				key_file.read(),
				password=pwd,
				backend=default_backend()
			)
			return key
	
	def publickeyFromText(self,text):
		public_key_bytes = bytes(text,encoding='utf8')
		return serialization.load_pem_public_key(data=public_key_bytes,backend=default_backend())

	def read_publickey(self,fname):
		with open(fname,'r') as f:
			text = f.read()
			return self.publickeyFromText(text)
			
	def create_privatekey(self, keylength=2048):
		return rsa.generate_private_key(
			public_exponent=65537,
			key_size=keylength,
			backend=default_backend()
			)
	
	def create_publickey(self,private_key):
		return private_key.public_key()
		
	def encode_bytes(self, public_key, bdata):
		return public_key.encrypt(bdata,
			padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			))

	def encode(self,public_key,text):
		message_bytes = bytes(text, encoding='utf8') if not isinstance(text, bytes) else text
		cdata = self.encode_bytes(public_key, message_bytes)
		return str(base64.b64encode(cdata), encoding='utf-8')
		
	def decode_bytes(self, private_key, bdata):
		return private_key.decrypt(
			bdata,padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			)
		)
		
	def decode(self,private_key,cipher):
		cipher = cipher.encode('utf8') if not isinstance(cipher, bytes) else cipher
		ciphertext_decoded = base64.b64decode(cipher)
		plain_text = self.decode_bytes(private_key, ciphertext_decoded)
		return str(plain_text, encoding='utf8')
		
	def sign_bdata(self, private_key, data_to_sign):
		s = private_key.sign(data_to_sign,
			  padding.PSS(
				  mgf=padding.MGF1(hashes.SHA256()),
				  salt_length=padding.PSS.MAX_LENGTH
			  ),
			  hashes.SHA256()
		)
		return s

	def sign(self,private_key,message):
		data_to_sign = bytes(message, encoding='utf8') if not isinstance(
			message, 
			bytes
		) else message
		signature = str(
			base64.b64encode(self.sign_bdata(private_key, data_to_sign)),
			encoding='utf8'
		)
		return signature
	
	def check_sign_bdata(self, public_key, bdata, sign):
		try:
			r = public_key.verify(sign, bdata, 
			  padding.PSS(
				  mgf=padding.MGF1(hashes.SHA256()),
				  salt_length=padding.PSS.MAX_LENGTH
			  ),
			  hashes.SHA256()
			)
			# print('verify return=', r) r is None
			return True
		except InvalidSignature as e:
			return False

	def check_sign(self,public_key,plain_text,signature):
			plain_text_bytes = bytes(
				plain_text, 
				encoding='utf8'
			) if not isinstance(plain_text, bytes) else plain_text
			signature = base64.b64decode(
				signature
			) if not isinstance(signature, bytes) else signature
			return self.check_sign_bdata(public_key, plain_text_bytes, \
					signature)
			
if __name__ == '__main__':
	import os
	prikey1_file = os.path.join(os.path.dirname(__file__),'..','test', 'prikey1.rsa')
	r = RSA()
	mpri = r.create_privatekey(4096)
	mpub = r.create_publickey(mpri)
	
	zpri = r.create_privatekey(4096)
	zpub = r.create_publickey(zpri)
	
	l = 100
	while True:
		text = 'h' * l
		cipher = r.encode(mpub,text)
		ntext = r.decode(mpri,cipher)
		print('textlen=', l, 'encode text=', text, \
				'decode result=', ntext,
				'cyber size=', len(cipher),
				'check if equal=', text==ntext)
		signature = r.sign(zpri,text)
		check = r.check_sign(zpub,text,signature)
		print('sign and verify=',len(signature),check)
		l += 1

