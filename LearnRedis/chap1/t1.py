import redis

conn = redis.Redis(db=0)

conn.sadd("set-key","val1")
conn.sadd("set-key","val2")
set1=conn.smembers("set-key")
print(set1)
conn.srem("set-key","val1")
set1=conn.smembers("set-key")
print(set1)
set1=conn.smembers("myset")
print(set1)
