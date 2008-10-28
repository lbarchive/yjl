import datetime
import logging
import pickle
import re

from google.appengine.api import memcache
from google.appengine.api import urlfetch 

#from lastweet import user
import user
import twitter_client.service

import gdata.alt.appengine


# in second
MIN_INTERVAL = 1.0
message_body_pattern = re.compile('@[^ ]+ (.*)')

def has(username):
  """Returns if username is in queue"""
  q = memcache.get('q')
  if q is None or len(q) == 0:
    curr = memcache.get('q_current')
    if curr is None:
      return False
    return curr[0] == username
  return username in q


def add(u):
  """Put a user in queue"""
  q = memcache.get('q') or []
  if u.username in q:
    return
  q.append(u.username)
  memcache.set('q', q)

def process():
  """Process a bit"""
  # Check if it's time to process
  last_process = memcache.get('q_last')
  if last_process:
    # Has q_last, then check it
    diff = datetime.datetime.utcnow() - last_process
    seconds = diff.days * 86400 + diff.seconds + diff.microseconds / 1000000.0
    if seconds < MIN_INTERVAL:
      logging.debug('Ping too quick, skipped')
      return
  memcache.set('q_last', datetime.datetime.utcnow())

  curr = memcache.get('q_current')
  if curr is None:
    q = memcache.get('q') or []
    if len(q) == 0:
      # Nothing in queue
      logging.debug('No item in queue, skipped')
      return
    username = q.pop(0)
    u = user.get(username)
    if not u:
      # No such user TODO log error
      return
    # Retrieve the friends list
    friends = u._friends
    # TODO Should drop protected friends?
    curr = (u.username, friends, [])
    memcache.set('q', q)
    memcache.set('q_current', curr)
  # Start to process a bit
  curr_f = curr[1].popitem()

  client = twitter_client.service.TwitterService(application_name='LasTweet/0')
  gdata.alt.appengine.run_on_appengine(client)
  search = client.NewSearch()
  search.keywords = ['from:' + curr[0], 'to:' + curr_f[0]]
  search.rpp = 1

  result = search.Search()
  if len(result.entry) == 1:
    entry = result.entry[0]
    # Process the message
    # Get the unicode string
    msg = entry.title.text.decode('utf-8')
    # Remove the @reply
    msg = message_body_pattern.match(msg).group(1)
    # Truncate
    if len(msg) > 50:
      msg = msg[:47] + '...'
    else:
      msg = msg[:50]
    curr[2].append({
        'username': curr_f[0],
        'msg': msg,
        'msg_id': int(entry.GetMessageID()),
        'published': entry.published.Get(),
        'profile_image': curr_f[1],
        })
  else:
    curr[2].append({
        'username': curr_f[0],
        'msg': '',
        'msg_id': 0,
        'published': None,
        'profile_image': curr_f[1],
        })

  # If there is no more in curr[1]
  if not curr[1]:
    # TODO sort result
    u = user.get(curr[0])
    u.tweets = pickle.dumps(sort_messages(curr[2]))
    u.last_updated = datetime.datetime.utcnow()
    u.put()
    # End of updating for this user
    memcache.delete('q_current')
  else:
    memcache.set('q_current', curr)

def get_status():
  """Returns current status of queue
  A 2-tuple, first element is length of queue, second is length of current processed username"""
  q = memcache.get('q')
  curr = memcache.get('q_current')
  q_l = 0
  curr_l = 0
  if q:
    q_l = len(q)
  if curr:
    curr_l = len(curr[1])
  return (q_l, curr_l)

def sort_messages(msgs):
  # FIXME make me pretty
  def cmp(x, y):
    x = x['published']
    y = y['published']
    if x is None and y is not None:
      return -1
    if x is not None and y is None:
      return 1
    if x is None and y is None:
      return 0
    if x > y:
      return 1
    if x < y:
      return -1
    if x == y:
      return 0
  msgs.sort(cmp)
  return msgs
