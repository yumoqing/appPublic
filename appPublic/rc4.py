# -*- coding: utf-8 -*-  
import random, base64  
from hashlib import sha1  
 
class RC4:
	def __init__(self,key='1234567890',data_coding='utf8'):
		self.bcoding = 'iso-8859-1'
		self.dcoding = data_coding
		self.key = key.encode(self.bcoding)
		self.salt = b'AFUqx9WZuI32lnHk'
	
	def _crypt(self,data,key):
		"""RC4 algorithm return bytes"""
		if type(data)==type(''):
			data = data.encode(self.dcoding)
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
  
	def encode(self,data, encode=base64.b64encode, salt_length=16):  
		"""RC4 encryption with random salt and final encoding"""  
		#salt = ''  
		#for n in range(salt_length):  
		#	salt += chr(random.randrange(256))
		#salt = salt.encode(self.bcoding)
		a = sha1(self.key + self.salt)
		k = a.digest()
		data = self.salt + self._crypt(data, k)
		
		if encode:  
			data = encode(data)
		return data.decode(self.dcoding)

	def decode(self,data, decode=base64.b64decode, salt_length=16):  
		"""RC4 decryption of encoded data"""  
		if decode:  
			data = decode(data)  
		salt = data[:salt_length]
		a = sha1(self.key + self.salt)
		k = a.digest() #.decode('iso-8859-1')
		r = self._crypt(data[salt_length:], k)
		return r.decode(self.dcoding)

  
if __name__=='__main__':  
	# 需要加密的数据  
	data = '''hello python 爱的实打实大师大师大师的发送到发送到而非个人格个二哥而而二哥而个人各位,UDP是一种无连接对等通信协议，没有服务器和客户端概念，通信的任何一方均可通过通信原语直接和其他方通信
	
HOME FAQ DOCS DOWNLOAD 
 

index
next |
previous |
Twisted 18.9.0 documentation » Twisted Names (DNS) » Developer Guides » 

Creating a custom server
The builtin DNS server plugin is useful, but the beauty of Twisted Names is that you can build your own custom servers and clients using the names components.
In this section you will learn about the components required to build a simple DNS server.
You will then learn how to create a custom DNS server which calculates responses dynamically.
A simple forwarding DNS server
Lets start by creating a simple forwarding DNS server, which forwards all requests to an upstream server (or servers).
simple_server.py
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
An example of a simple non-authoritative DNS server.
"""

from twisted.internet import reactor
from twisted.names import client, dns, server


def main():
    """
    Run the server.
    """
    factory = server.DNSServerFactory(
        clients=[client.Resolver(resolv='/etc/resolv.conf')]
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(10053, protocol)
    reactor.listenTCP(10053, factory)

    reactor.run()


if __name__ == '__main__':
    raise SystemExit(main())
In this example we are passing a client.Resolver instance to the DNSServerFactory and we are configuring that client to use the upstream DNS servers which are specified in a local resolv.conf file.
Also note that we start the server listening on both UDP and TCP ports. This is a standard requirement for DNS servers.
You can test the server using dig. For example:
$ dig -p 10053 @127.0.0.1 example.com SOA +short
sns.dns.icann.org. noc.dns.icann.org. 2013102791 7200 3600 1209600 3600
A server which computes responses dynamically
Now suppose we want to create a bespoke DNS server which responds to certain hostname queries by dynamically calculating the resulting IP address, while passing all other queries to another DNS server. Queries for hostnames matching the pattern workstation{0-9}+ will result in an IP address where the last octet matches the workstation number.
We’ll write a custom resolver which we insert before the standard client resolver. The custom resolver will be queried first.
Here’s the code:
override_server.py
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
An example demonstrating how to create a custom DNS server.

The server will calculate the responses to A queries where the name begins with
the word "workstation".

Other queries will be handled by a fallback resolver.

eg
    python doc/names/howto/listings/names/override_server.py

    $ dig -p 10053 @localhost workstation1.example.com A +short
    172.0.2.1
"""

from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server



class DynamicResolver(object):
    """
    A resolver which calculates the answers to certain queries based on the
    query type and name.
    """
    _pattern = 'workstation'
    _network = '172.0.2'

    def _dynamicResponseRequired(self, query):
        """
        Check the query to determine if a dynamic response is required.
        """
        if query.type == dns.A:
            labels = query.name.name.split('.')
            if labels[0].startswith(self._pattern):
                return True

        return False


    def _doDynamicResponse(self, query):
        """
        Calculate the response to a query.
        """
        name = query.name.name
        labels = name.split('.')
        parts = labels[0].split(self._pattern)
        lastOctet = int(parts[1])
        answer = dns.RRHeader(
            name=name,
            payload=dns.Record_A(address=b'%s.%s' % (self._network, lastOctet)))
        answers = [answer]
        authority = []
        additional = []
        return answers, authority, additional


    def query(self, query, timeout=None):
        """
        Check if the query should be answered dynamically, otherwise dispatch to
        the fallback resolver.
        """
        if self._dynamicResponseRequired(query):
            return defer.succeed(self._doDynamicResponse(query))
        else:
            return defer.fail(error.DomainError())



def main():
    """
    Run the server.
    """
    factory = server.DNSServerFactory(
        clients=[DynamicResolver(), client.Resolver(resolv='/etc/resolv.conf')]
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(10053, protocol)
    reactor.listenTCP(10053, factory)

    reactor.run()



if __name__ == '__main__':
    raise SystemExit(main())
Notice that DynamicResolver.query returns a Deferred. On success, it returns three lists of DNS records (answers, authority, additional), which will be encoded by dns.Message and returned to the client. On failure, it returns a DomainError, which is a signal that the query should be dispatched to the next client resolver in the list.
Note
The fallback behaviour is actually handled by ResolverChain.
ResolverChain is a proxy for other resolvers. It takes a list of IResolver providers and queries each one in turn until it receives an answer, or until the list is exhausted.
Each IResolver in the chain may return a deferred DomainError, which is a signal that ResolverChain should query the next chained resolver.
The DNSServerFactory constructor takes a list of authoritative resolvers, caches and client resolvers and ensures that they are added to the ResolverChain in the correct order.
Let’s use dig to see how this server responds to requests that match the pattern we specified:
$ dig -p 10053 @127.0.0.1 workstation1.example.com A +short
172.0.2.1

$ dig -p 10053 @127.0.0.1 workstation100.example.com A +short
172.0.2.100
And if we issue a request that doesn’t match the pattern:
$ dig -p 10053 @localhost www.example.com A +short
93.184.216.119
Further Reading
For simplicity, the examples above use the reactor.listenXXX APIs. But your application will be more flexible if you use the Twisted Application APIs, along with the Twisted plugin system and twistd. Read the source code of names.tap to see how the twistd names plugin works.
Table Of Contents
Creating a custom server
A simple forwarding DNS server
A server which computes responses dynamically
Further Reading
Previous topic
Creating and working with a names (DNS) server
Next topic
Examples
This Page
Show Source
Quick search
  
Enter search terms or a module, class or function name. 


Site design
By huw.wilkins. 
'''
	# 密钥 
	key = '123456'  
	rc4 = RC4(key)
	print(data)
	# 加码  
	encoded_data = rc4.encode(data)  
	print(encoded_data,len(encoded_data) )
	# 解码  
	decoded_data = rc4.decode(encoded_data)  
	print(decoded_data)