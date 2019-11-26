import redis

conn = redis.Redis(db=0)

conn.zinterstore('test',{'test':0.5})