from google.appengine.api import memcache
from google.appengine.api import urlfetch 

from lastweet import user
import twitter_client.service

def has(username):
  """Returns if username is in queue"""
  q = memcache.get('q')
  if q is None or len(q):
    return False
  return username in q


def add(u):
  """Put a user in queue
  Not reliable.
  """
  q = memcache.get('q') or []
  if u.username in q:
    return
  q.append(u.username)
  memcache.set('q', q)

def process():
  """Process a bit"""
  curr = memcache.get('q_current')
  if curr is None:
    q = memcache.get('q') or []
    if len(q) == 0:
      # Nothing in queue
      return
    username = q.pop(0)
    u = user.has(username)
    if not u:
      # No such user TODO log error
      return
    # Retrieve the friends list
    friends = u._friends
    curr = (u.username, friends, [])
  # Start to process a bit
  curr_f = curr[1].pop(0)
  memcache.set('q_current', curr)

  client = twitter_client.service.TwitterService(application_name='LasTweet/0')
  search = client.NewSearch()
  search.keywords = ['from:' + curr[0], 'to:' + curr_f[0]]
  serach.rpp = 1

  result = search.Search()
  if len(result.entry) == 1:
    entry = result.entry
    entry.title.text[:50]
    entry.published.Get()
    (result.
