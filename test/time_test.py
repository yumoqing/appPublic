import time

def f(timeout=2):
	t1 = time.time()
	t = t1
	t1 += timeout
	while t1 > t:
		print(t, t1)
		time.sleep(1)
		t = time.time()

if __name__ == '__main__':
	f()
