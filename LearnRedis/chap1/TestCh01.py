import redis
import time
import unittest

#define constant 
ONE_WEEK_IN_SECONDS=7*86400
VOTE_SCORE=432
ARTICLE_PER_PAGE=25

def post_article(conn,user,title,link):
    #generate article id
    article_id=str(conn.incr('article:'))

    #generate the set key for SET voted
    voted='voted:'+article_id
    #add the author to SET voted storing voted user
    conn.sadd(voted,user)
    #set the SET voted to be exipred after one week to avoid being voted
    conn.expire(voted,ONE_WEEK_IN_SECONDS)

    #add article to HASH
    article='article:'+article_id
    now=time.time()
    conn.hmset(article,
                {'title':title,
                 'link':link,
                 'poster':user,
                 'time':now,
                 'votes':1,})

    #add article to zset
    conn.zadd('score:',{article:now+VOTE_SCORE})
    conn.zadd('time:',{article:now})

    return article_id

def get_articles(conn,page,order='score:'):
    start = (page-1)*ARTICLE_PER_PAGE
    end = start + page*ARTICLE_PER_PAGE

    articles = []

    ids = conn.zrevrange(order,start,end)

    for id in ids:
        article_data = conn.hgetall(id)
        article_data['id'] = id
        articles.append(article_data)

    return articles

def article_vote(conn,user,article):
    #check if the article is posted more than 7 days
    post_date=conn.zscore('time:',article)
    now=time.time()
    if(now < post_date - ONE_WEEK_IN_SECONDS):
        return
    
    #if the article is posted less than 7 days
    #add user to SET voted
    article_id=article.partition(':')[-1]
    voted_set='voted:'+article_id
    score_zset='score:'
    if conn.sadd(voted_set,user):
        #if user is added to SET voted successfully
        #update article.votes
        conn.hincrby(article,'votes',1)
        conn.zincrby(score_zset,VOTE_SCORE,article)

def add_remove_groups(conn,article_id,to_add=[],to_remove=[]):
    article = 'article:'+article_id

    for group in to_add:
        conn.sadd('group:'+group,article)

    for group in to_remove:
        conn.srem('group:'+group,article)

def get_group_articles(conn,group,page,order='score:'):
    key=order+group

    if not conn.exists(key):
        conn.zinterstore(key,['group:'+group,order],aggregate='max')
        conn.expire(key,60)

    return get_articles(conn,page,key)

class TestCh01(unittest.TestCase):
    def setUp(self):
        import redis
        self.conn=redis.Redis(db=0)
    
    def tearDown(self):
        del self.conn
        print()
        print()

    def test_article_functionality(self):
        conn=self.conn

        ############################################################################
        #article vote
        ############################################################################

        #initialization
        user='BillHu'
        title='Redis in action'
        link='https://www.163.com/RedisInAction'

        #post article
        article_id=post_article(conn,user,title,link)
        article_hash='article:'+article_id
        voted_set='voted:'+article_id
        time_zset='time:'
        score_zset='score:'

        #check article
        print("We posted a new article with id:",article_id)
        print()
        self.assertTrue(article_id)

        print("Its HASH looks like:")
        r=conn.hgetall(article_hash)
        print(r)
        self.assertTrue(r)

        #check voted
        print('User:BillHu is added to '+voted_set)
        r=conn.smembers(voted_set)
        print(r)
        self.assertTrue(conn.sismember(voted_set,user))
        print()

        #check score
        print(article_hash+' is added to '+score_zset)
        r=conn.zrange(score_zset,0,-1,False,True)
        print(r)
        print()

        #check time
        print(article_hash+' is added to '+time_zset)
        r=conn.zrange(time_zset,0,-1,False,True)
        print(r)
        print()

        ############################################################################
        #vote articke
        ############################################################################
        voter='sofica'
        article_vote(conn,voter,article_hash)

        #check voted
        print('User:'+voter+' is added to '+voted_set)
        r=conn.smembers(voted_set)
        print(r)
        self.assertTrue(conn.sismember(voted_set,voter))
        print()

        #check article
        print(article_hash+' is updated by adding 1 votes')
        r=conn.hgetall(article_hash)
        print(r)
        print()

        #check score
        print('Article '+article_id+' is updated in '+score_zset)
        r=conn.zrange(score_zset,0,-1,False,True)
        print(r)
        print()

        ############################################################################
        #article add remove to group
        ############################################################################
        #initialization
        user1='User1'
        title1='Title1 in action'
        link1='https://www.163.com/Title1InAction'
        user2='User2'
        title2='Title2 in action'
        link2='https://www.163.com/Title2InAction'
        user3='User3'
        title3='Title3 in action'
        link3='https://www.163.com/Title3InAction'

        #post article
        article_id1=post_article(conn,user1,title1,link1)
        article_id2=post_article(conn,user2,title2,link2)
        article_id3=post_article(conn,user3,title3,link3)

        #add new articles to new-group
        add_remove_groups(conn,article_id1,['new-group'])
        add_remove_groups(conn,article_id2,['new-group'])
        add_remove_groups(conn,article_id3,['new-group'])

        #get articles from new-group
        articles = get_group_articles(conn,'new-group',1)
        print('Articles fetched from new-group:')
        print(articles)

        #clean up
        to_del = (
            conn.keys('time:*') + conn.keys('voted:*') + conn.keys('score:*') + 
            conn.keys('article:*') + conn.keys('group:*')
        )
        
        if to_del:
            conn.delete(*to_del)

if __name__ == '__main__':
    unittest.main()