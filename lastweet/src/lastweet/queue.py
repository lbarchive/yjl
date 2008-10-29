import datetime
import logging
import pickle
import re

from google.appengine.api import memcache
from google.appengine.api import urlfetch 
from google.appengine.ext import db

#from lastweet import user
import user
from lastweet import util

import twitter_client.service

import gdata.alt.appengine


# in second
PROCESS_AUTO_QUEUE_INTERVAL = 3600
PROCESS_MAIL_INTERVAL = 600
PROCESS_QUEUE_INTERVAL = 1
# 2000 / 86400 * 600 ~= 13.88 mails
MAILS_PER_PROCESS = 15

FETCH_TIMEOUT = 30

message_body_pattern = re.compile('@[^ ]+ (.*)')


def has(username):
  """Returns if username is in queue"""
  q = memcache.get('q')
  if q is None or len(q) == 0:
    return False
  return username.lower() in q


def lock(key, timeout=None, force=False, wait_interval=0.1):
  """Lock helper
  timeout in second, None is never timeout
  force
  """
  start = datetime.datetime.utcnow()
  while not memcache.add(key, datetime.datetime.utcnow()):
    # There already is 'qlock' in memcache
    if timeout is not None or (datetime.datetime.utcnow() - start).seconds >= timeout:
      if not force:
        # Can't acquire lock
        return False
      # Force to acquire lock
      # FIXME still has possiblity of two to get lock forcibly in an about time
      memcache.set(key, datetime.datetime.utcnow());
      return True
    time.sleep(wait_interval)
  return True

# TODO with?
def unlock(key):
  memcache.delete(key)


def add(u):
  """Put a user in queue"""
  if has(u.username):
    # Already in queue
    return False
  if not lock('qlock', 5, True):
    # Cannot get lock, should not happen
    return False
  q = memcache.get('q') or []
  q.append(u.username.lower())
  memcache.set('q', q)
  unlock('qlock')
  return True


def remove(u):
  """Remove a user from queue

  Remove username from queue
  Remove q_username from memcache
  Remove qlock_username from memcache
  """
  if isinstance(u, (str, unicode)):
    username = u
  else:
    username = u.username
  username = username.lower()

  if not has(username):
    # Not in queue
    return False
  if not lock('qlock', 5, True):
    # Cannot get lock, should not happen
    return False

  memcache.delete('q_' + username)
  unlock('qlock_' + username)

  q = memcache.get('q') or []
  q.remove(username)
  memcache.set('q', q)
  unlock('qlock')
  return True

  
def lock_one_username():
  q = memcache.get('q') or []
  for username in q:
    locked_time = memcache.get('qlock_' + username)
    if locked_time is not None:
      if (datetime.datetime.utcnow() - locked_time).seconds >= FETCH_TIMEOUT:
        # Force to acquire, if locked more than FETCH_TIMEOUT ago
        memcache.set('qlock_' + username, datetime.datetime.utcnow())
        return username
      else:
        continue
    if lock('qlock_' + username, 0):
      # Get the lock
      return username
  return False


def process():
  process_queue()
  process_auto_queue()
  process_mail()


def process_auto_queue():
  """Find people need to be updated"""
  last_process = memcache.get('last_process_auto_queue')
  if last_process and util.td_seconds(last_process) < PROCESS_AUTO_QUEUE_INTERVAL:
    return
  logging.debug('Processing auto queue')
  memcache.set('last_process_auto_queue', util.now())

  now = util.now()
  update_after = now - datetime.timedelta(seconds=user.UPDATE_INTERVAL)

  # Queue those needs get updated, which have email address
  #q = user.User.gql("WHERE email > '' AND last_updated < :1 AND last_updated > ''", update_after)
  q = user.User.gql("WHERE last_updated < :1 AND last_updated > ''", update_after)
  count = 0
  offset = 0
  while count < 50:
    for u in q.fetch(50, offset * 50):
      if u.email:
        add(u)
        count += 1
        if count >= 50:
          break
    else:
      break
    offset += 1

  # Queue those never get updated
  q = user.User.gql("WHERE last_updated < ''")
  for u in q.fetch(50):
    add(u)


def process_mail():
  """Send some mails"""
  last_process = memcache.get('last_process_mail')
  if last_process and util.td_seconds(last_process) < PROCESS_MAIL_INTERVAL:
    return
  logging.debug('Processing mail')
  memcache.set('last_process_mail', util.now())

  now = util.now()
  mail_before = now - datetime.timedelta(seconds=user.MAIL_INTERVAL)
  update_after = now - datetime.timedelta(seconds=user.UPDATE_INTERVAL)

  # Queue those needs get updated, which have email address
  #q = user.User.gql("WHERE email > '' AND last_updated >= :1 AND last_mailed < :2", update_after, mail_before)
  q = user.User.gql("WHERE last_mailed < :1", mail_before)
  count = 0
  offset = 0
  while count < MAILS_PER_PROCESS:
    for u in q.fetch(50, offset * 50):
      if u.email and u.last_updated and u.last_updated >= update_after:
        user.try_mail(u)
        count += 1
        if count >= MAILS_PER_PROCESS:
          break
    else:
      break
    offset += 1


def process_queue():
  """Process a bit"""
  # Check if it's time to process
  last_process = memcache.get('last_process_queue')
  if last_process and util.td_seconds(last_process) < PROCESS_QUEUE_INTERVAL:
    return
  memcache.set('last_process_queue', util.now())

  username = lock_one_username()
  if not username:
    logging.debug('No item in queue, skipped')
    return

  curr = memcache.get('q_' + username)
  if curr is None:
    u = user.get(username)
    if not u:
      logging.debug('No such user %s in db' % username)
      remove(username)
      return
    # Retrieve the friends list
    friends = u._friends
    # TODO Should drop protected friends?
    curr = (u.username, friends, [])
    memcache.set('q_' + username, curr)
  # Start to process a bit
  curr_f = curr[1].popitem()

  client = twitter_client.service.TwitterService(application_name='LasTweet/0')
  gdata.alt.appengine.run_on_appengine(client)
  search = client.NewSearch()
  search.keywords = ['from:' + curr[0], 'to:' + curr_f[0]]
  search.rpp = 1

  new_tweet = {
      'username': curr_f[0],
      'msg': '',
      'msg_id': 0,
      'published': None,
      'profile_image': curr_f[1],
      }
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
    new_tweet['msg'] = msg
    new_tweet['msg_id'] = int(entry.GetMessageID())
    new_tweet['published'] = entry.published.Get()
  curr[2].append(new_tweet)

  # If there is no more in curr[1]
  if not curr[1]:
    tweets = pickle.dumps(sort_messages(curr[2]))
    u = db.run_in_transaction(user.transaction_update_tweets, curr[0], tweets)
    user.try_mail(u)
    # End of updating for this user
    remove(u)
  else:
    memcache.set('q_' + username, curr)
  unlock('qlock_' + username)


def get_status():
  """Returns current length of queue"""
  q = memcache.get('q') or []
  return len(q)


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
