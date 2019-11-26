import redis
import time
import unittest
import uuid
import threading

def check_token(conn, token):
    return conn.hget('login:',token)

def update_token(conn,token,user,item=None):
    timestamp = time.time()
    conn.hset('login:',token,user)
    conn.zadd('recent:', {token:timestamp})

    if item:
        conn.zadd('viewed:'+token,{item:timestamp})
        conn.zremrangebyrank('viewed:'+token,0,-26)

QUIT = False
LIMIT = 10000000

def clean_sessions(conn):
    while not QUIT:
        size = conn.zcard('recent:')
        #sleep 1 second if the logoned token is not exceed the LIMIT
        if size < LIMIT:
            time.sleep(1)
            continue

        #find out the logoned token list to be removed
        end_index = min(size - LIMIT, 100)
        tokens = conn.zrange('recent:',0,end_index-1)
        
        #remove
        for token in tokens:
            #remove viewed information
            conn.delete('viewed:'+str(token))
            #remove login information
            conn.hdel('login:',token)
            #remove recent login information
            conn.zrem('recent:',token)

def add_to_cart(conn,session,item,count):
    if count <= 0:
        conn.hrem('cart:'+session,item)
    else:
        conn.hset('cart:'+session,item,count)

def clean_full_sessions(conn):
    while not QUIT:
        size = conn.zcard('recent:')
        #sleep 1 second if the logoned token is not exceed the LIMIT
        if size < LIMIT:
            time.sleep(1)
            continue

        #find out the logoned token list to be removed
        end_index = min(size - LIMIT, 100)
        tokens = conn.zrange('recent:',0,end_index-1)
            
        #remove
        for token in tokens:
            #remove viewed information
            conn.delete('viewed:'+str(token.decode()))
            #remove login information
            conn.hdel('login:',token)
            #remove recent login information
            conn.zrem('recent:',token)
            #remove cart information
            conn.delete('cart:'+str(token.decode()))

class TestCh02(unittest.TestCase):
    def setUp(self):
        import redis
        self.conn=redis.Redis(db=0)
        
    def tearDown(self):
        conn = self.conn
        
        to_del = (
            conn.keys('login:*') + conn.keys('recent:*') + conn.keys('viewed:*') +
            conn.keys('cart:*') + conn.keys('cache:*') + conn.keys('delay:*') + 
            conn.keys('schedule:*') + conn.keys('inv:*'))

        if to_del:
            self.conn.delete(*to_del)

        del self.conn

        global QUIT, LIMIT

        QUIT = False
        LIMIT = 10000000
        print()
        print()

    def test_logon_functionality(self):
        conn = self.conn
        token = str(uuid.uuid4())
        global LIMIT, QUIT

        #logon to update token
        update_token(conn, token, 'username', 'itemX')
        print("We just logged-in/updated token:", token)
        print("For user:", 'username')
        print()

        #get username by token
        print("What username do we get when we look-up that token?")
        r = check_token(conn, token)
        print(r)
        print()
        self.assertTrue(r)

        #test clean_session
        print("Let's drop the maximum number of cookies to 0 to clean them out")
        print("We will start a thread to do the cleaning, while we stop it later")

        LIMIT = 0
        t = threading.Thread(target=clean_sessions, args=(conn,))
        t.setDaemon(1) # to make sure it dies if we ctrl+C quit
        t.start()
        time.sleep(1)
        QUIT = True
        time.sleep(2)
        if t.isAlive():
            raise Exception("The clean sessions thread is still alive?!?")

        s = conn.hlen('login:')
        print("The current number of sessions still available is:", s)
        self.assertFalse(s)

    def test_shopping_cart_cookies(self):
        conn = self.conn
        global LIMIT, QUIT
        token = str(uuid.uuid4())

        print("We'll refresh our session...")
        update_token(conn, token, 'username', 'itemX')
        print("And add an item to the shopping cart")
        add_to_cart(conn, token, "itemY", 3)
        r = conn.hgetall('cart:' + token)
        print("Our shopping cart currently has:", r)
        print()

        self.assertTrue(len(r) >= 1)

        print("Let's clean out our sessions and carts")
        LIMIT = 0
        t = threading.Thread(target=clean_full_sessions, args=(conn,))
        t.setDaemon(1) # to make sure it dies if we ctrl+C quit
        t.start()
        time.sleep(1)
        QUIT = True
        time.sleep(2)
        if t.isAlive():
            raise Exception("The clean sessions thread is still alive?!?")

        r = conn.hgetall('cart:' + token)
        print("Our shopping cart now contains:", r)

        self.assertFalse(r)

if __name__ == '__main__':
    unittest.main()