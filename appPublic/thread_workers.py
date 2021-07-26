import time
import threading
import random
from appPublic.background import Background

class ThreadWorkers:
	def __init__(self, worker_cnt=10):
		self.semaphore = threading.Semaphore(value=worker_cnt)
		self.co_worker = 0
	def _do(self, func, *args, **kwargs):
		self.co_worker += 1
		func(*args, **kwargs)
		self.co_worker -= 1
		self.semaphore.release()

	def do(self, func, *args, **kwargs):
		self.semaphore.acquire()
		b = Background(self._do, func, *args, **kwargs)
		b.start()

	def get_workers(self):
		return self.co_worker

if __name__ == '__main__':
	def k(worker):
		t = random.randint(1,4)
		print('current workers=',worker.get_workers(), 'sleep=', t)
		time.sleep(t)

	w = ThreadWorkers()
	for i in range(100000):
		w.do(k, w)

