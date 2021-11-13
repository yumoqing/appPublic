# zmq_topic
zmq_topic implements a topic message machine, it need a TopicServer with created using a server address, publish_port and subscrible_port, and one or more publisher with can publish topiced message and one or more topic message subscriber which comsumes topiced message.

If the server gone, subscriber will not received message, and when the server restart, subscriber will received message again, but the message will miss send by publisher when the server is down.

## Usage examples

topic server
```
from appPublic.zmq_topic import TopicServer

x = TopicServer(address='127.0.0.1', pub_port=5678, sub_port=5679)
```

publisher
```
import time
from appPublic.zmq_topic import TopicPublisher
def test_publish(topic):
	p = TopicPublisher(topic=topic, address='127.0.0.1', port=5678)
	cnt = 1
	while True:
		p.send(f'message {cnt}')
		time.sleep(1)
		cnt += 1

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 2:
		print(f'Usage:\n{sys.argv[0]} topic')
		sys.exit(1)
	test_publish(sys.argv[1])

```
subscriber
```
from appPublic.zmq_topic import TopicSubscriber
def test_subscribe(topic):
	def print_message(msg):
		print(msg)

	s = TopicSubscriber(topic=topic, address='127.0.0.1', 
				port=5679, callback=print_message)
	s.run()

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 2:
		print(f'Usage:\n{sys.argv[0]} topic')
		sys.exit(1)
	test_subscribe(sys.argv[1])

```
## TopicServer
## ConfiguredTopicServer
## TopicPublisher
## ConfiguredTopicPublisher
## TopicSubscribler
## ConfiguredTopicSubscribler

