import base64
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
"""
use AES ECBmode to encrypt and decrype
"""

def pad(data: bytes) -> bytes:
	padder = padding.PKCS7(128).padder()  # AES 块大小是 128 bits
	return padder.update(data) + padder.finalize()

def unpad(data: bytes) -> bytes:
	unpadder = padding.PKCS7(128).unpadder()
	return unpadder.update(data) + unpadder.finalize()

def len32(key):
	cnt = len(key)
	if cnt < 32:
		key += b'*' * (32 - cnt)
	elif cnt > 32:
		key = key[:32]
	return key

def aes_encrypt_ecb(key: bytes, plaintext: str) -> bytes:
	key = len32(key) 
	cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
	encryptor = cipher.encryptor()
	padded_data = pad(plaintext.encode('iso-8859-1'))
	return encryptor.update(padded_data) + encryptor.finalize()

def aes_decrypt_ecb(key: bytes, ciphertext: bytes) -> str:
	key = len32(key) 
	cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
	decryptor = cipher.decryptor()
	padded_plain = decryptor.update(ciphertext) + decryptor.finalize()
	return unpad(padded_plain).decode('iso-8859-1')

def aes_encode_b64(key:str, text:str) -> str:
	key = key.encode('iso-8859-1')
	cyber = aes_encrypt_ecb(key, text)
	secret = cyber.decode('iso-8859-1')
	return base64.b64encode(cyber).decode('iso-8859-1')

def aes_decode_b64(key:str, b64str:str) -> str:
	key = key.encode('iso-8859-1')
	b64b = b64str.encode('iso-8859-1')
	cyber = base64.b64decode(b64b)
	return aes_decrypt_ecb(key, cyber)

if __name__ == '__main__':
	key = '67t832ufbj43riu8ewrg'
	o = 'this is s test string'
	b = aes_encode_b64(key, o)
	t = aes_decode_b64(key, b)
	print(f'{o=},{b=},{t=}')
