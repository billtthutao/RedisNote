import redis
import time
import threading

def notrans():
    conn = redis.Redis()
    conn.incr('notrans:')
    time.sleep(0.2)
    x=conn.incr('notrans:',-1)
    print(x)

if __name__ == '__main__':
    for i in range(5):
        threading.Thread(target=notrans).start()
        #time.sleep(0.5)