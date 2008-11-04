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

import base64
import datetime
import logging
import os
import pickle
import simplejson as json

from google.appengine.api import mail
from google.appengine.api import urlfetch 
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import config
from lastweet import queue
from lastweet import util


MAIL_INTERVAL = 14 * 86400
UPDATE_INTERVAL = 86400


class User(db.Model):
  username = db.StringProperty()
  profile_image = db.StringProperty()
  email = db.StringProperty()
  last_mailed = db.DateTimeProperty()
  last_updated = db.DateTimeProperty()
  tweets = db.TextProperty()

  def _get_tweets(self):
    if self.tweets:
      # No need to Copy the self.tweets is important to avoid KeyError: '\x00'
      # on Production server
      # Fixing the encoding problem also fixing the KeyError above
      return pickle.loads(self.tweets.encode('latin-1'))

  def _set_tweets(self, new_tweets):
    if isinstance(new_tweets, (str, unicode)):
      self.tweets = new_tweets
    else:
      # a message with a degree symbol \xb0 cause encoding problem
      self.tweets = db.Text(pickle.dumps(new_tweets), encoding='latin-1')

  _tweets_ = property(_get_tweets, _set_tweets)

  @property
  def _queued(self):
    result = queue.has(self.username)
    logging.debug('%s in queue: %s' % (self.username, str(result)))
    return result

  @property
  def _friends(self):
    f = util.fetch(
        'http://twitter.com/statuses/friends/%s.json' % self.username,
        config.twitter_username, config.twitter_password)
    if f.status_code == 200:
      u_json = json.loads(f.content)
      # TODO error
      friends = dict(
          [(friend['screen_name'], friend['profile_image_url'])
              for friend in u_json])
      logging.debug('Retrievd %d friends of %s.' % (len(friends), self.username))
      return friends
    else:
      logging.debug('Cannot fetch friends of %s: %d' % (self.username, f.status_code))

  @property
  def _need_update(self):
    # Need update when 
    #  a) never updated
    #  b) longer than UPDATE_INTERVAL since last updated 
    if not self.last_updated or util.td_seconds(self.last_updated) > UPDATE_INTERVAL:
      return True
    return False

  @property
  def _need_mail(self):
    if not self.email:
      return False
    if not self.last_mailed or util.td_seconds(self.last_mailed) > MAIL_INTERVAL:
      return True
    return False
  # TODO add trymail here


def fix_key_name(key_name):
  if key_name[0] in '0123456789':
    key_name = '#' + key_name
  else:
    key_name = key_name
  return key_name.lower()


def get(username):
  if username:
    return User.get_by_key_name(fix_key_name(username))
  return None


def add(username):
  """Adds a new user
  If exists, then return that.
  If adds, also put in queue
  If errors, return the status code
  """
  username = username.lower()
  # make sure
  u = get(username)
  if u:
    return u
  logging.debug('Fetching %s for adding to db' % username)
  f = util.fetch(
      'https://twitter.com/users/show/%s.json' % username,
      config.twitter_username, config.twitter_password)
  if f.status_code == 200:
    u_json = json.loads(f.content)
    # Create new entry
    u = db.run_in_transaction(transaction_add_user,
        u_json['screen_name'], u_json['profile_image_url'])
    # Queue it
    queue.add(u)
    return u
  # Unknown error
  return f.status_code


def transaction_add_user(username, profile_image):
  user = User(key_name=fix_key_name(username))
  user.username = username
  user.profile_image = profile_image
  user.put()
  return user


def transaction_update_email(username, email):
  user = User.get_by_key_name(fix_key_name(username))
  user.email = email
  user.put()
  return user


def transaction_update_tweets(username, tweets):
  user = User.get_by_key_name(fix_key_name(username))
  user._tweets_ = tweets
  user.last_updated = util.now()
  user.put()
  return user


def transaction_remove_email(username):
  user = User.get_by_key_name(fix_key_name(username))
  user.email = None
  user.last_mailed = None
  user.put()
  return user


def transaction_mailed(username):
  user = User.get_by_key_name(fix_key_name(username))
  if user.email is None:
    return
  user.last_mailed = util.now()
  user.put()
  return user


def verify_twitter(username, password):
  f = util.fetch('https://twitter.com/account/verify_credentials.json', username, password)
  del password
  return f.status_code == 200


def try_mail(u):
  if u._need_update or not u._need_mail:
    return

  # FIXME don't hard-coded the sender
  # Filter tweets
  tweets = []
  if u.tweets:
    for tweet in u._tweets_:
      if tweet['published'] and util.td_seconds(tweet['published']) < MAIL_INTERVAL:
        continue
      tweets.append(tweet)

  if len(tweets):
    template_values = {
        'username': u.username,
        'last_updated': u.last_updated,
        'tweets': tweets,
        }
    path = os.path.join(os.path.dirname(__file__), 'mail.txt')
    body = template.render(path, template_values)

    if 'appspot.com' in os.environ.get('SERVER_NAME', ''):
      sender = "livibetter@gmail.com"
      to = "%s <%s>" % (u.username, u.email)
    else:
      sender = "livibetter@gmail.com"
      to = "%s" % u.email

    mail.send_mail(
        subject="Last Tweets Subscription",
        sender=sender,
        to=to,
        body=body)
  # Update mailed date
  db.run_in_transaction(transaction_mailed, u.username)
