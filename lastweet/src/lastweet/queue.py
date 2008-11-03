# LasTweet lists last tweets to friends
# Copyright (C) 2008  Yu-Jie Lin
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
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

# Somehow, there may be no a space betweet @ and message,
# So just assume valid characters of a Twitter account
message_body_pattern = re.compile('@[_a-zA-Z0-9]+ ?(.*)')


def has(username):
  """Returns 1-based position of username in queue"""
  q = memcache.get('q')
  if q is None or len(q) == 0:
    return False
  try:
    return q.index(username.lower()) + 1
  except ValueError:
    return 0


def lock(key, timeout=None, force=False, wait_interval=0.1):
  """Lock helper
  timeout in second, None is never timeout
  force
  """
  logging.debug('Trying to acquire lock %s' % key)
  start = util.now()
  while memcache.get(key):
    logging.debug('already has lock %s in memcache' % key)
    # There already is 'qlock' in memcache
    if timeout is not None or util.td_seconds(start) >= timeout:
      if not force:
        # Can't acquire lock
        logging.debug('cannot acquire lock %s' % key)
        return False
      # Force to acquire lock
      logging.debug('forcibly acquire lock %s' % key)
      break
    time.sleep(wait_interval)
  logging.debug('acquire lock %s' % key)
  memcache.set(key, util.now());
  return True

# TODO with?
def unlock(key):
  logging.debug('Unlocking %s' % key)
  logging.debug('Result: %d' % memcache.delete(key))


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
    logging.debug('Retrieving %s from db' % username)
    u = user.get(username)
    if not u._need_update:
      remove(u)
      continue
    logging.debug('Checking lock')
    locked_time = memcache.get('qlock_' + username)
    logging.debug('locked_time: %s' % locked_time)
    if locked_time:
      logging.debug('Locked, timeout?')
      # I don't think this would be used...
      if util.td_seconds(locked_time) >= FETCH_TIMEOUT:
        logging.debug('Yes, timed out')
        # Force to acquire, if locked more than FETCH_TIMEOUT ago
        memcache.set('qlock_' + username, util.now())
        return username
      else:
        continue
    else:
      logging.debug('locked_time does not have a value, force to acquire')
      memcache.set('qlock_' + username, util.now())
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
  q = user.User.gql("WHERE last_updated < :1 AND last_updated > DATE(1,1,1)", update_after)
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
  q = user.User.gql("WHERE last_updated < DATE(1,1,1)")
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
  # In case this user do have friends
  if curr[1]:
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
        'maggie': None,
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

    # Search for maggie ads
    search.keywords = ['from:' + curr_f[0], '#magpie']
    search.rpp = 10
    result = search.Search()
    for entry in result.entry:
      # If #magpie at beginning, then this is a possiblity; and a link as well
      if entry.title.text.find('#magpie') == 0 and entry.title.text.find('http://') >= 0:
        msg = entry.title.text.decode('utf-8')
        if len(msg) > 50:
          msg = msg[:47] + '...'
        else:
          msg = msg[:50]
        new_tweet['magpie'] = {
          'msg': msg,
          'msg_id': int(entry.GetMessageID()),
          'published': entry.published.Get(),
          }
        # Only store the last
        break
    curr[2].append(new_tweet)

  # If there is no more in curr[1]
  if not curr[1]:
    u = db.run_in_transaction(user.transaction_update_tweets, curr[0],
        sort_messages(curr[2]))
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
  if not msgs:
    return msgs
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
