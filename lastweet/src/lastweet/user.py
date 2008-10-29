import base64
import datetime
import logging
import simplejson as json

from google.appengine.api import mail
from google.appengine.api import urlfetch 
from google.appengine.ext import db

from lastweet import queue


MAIL_INTERVAL = 14


class User(db.Model):
  username = db.StringProperty()
  profile_image = db.StringProperty()
  email = db.StringProperty()
  last_mailed = db.DateTimeProperty()
  last_updated = db.DateTimeProperty()
  tweets = db.TextProperty()

  @property
  def _queued(self):
    result = queue.has(self.username)
    logging.debug('%s in queue: %s' % (self.username, str(result)))
    return result

  @property
  def _friends(self):
    f = urlfetch.fetch('http://twitter.com/statuses/friends/%s.json' % self.username)
    if f.status_code == 200:
      u_json = json.loads(f.content)
      # TODO error
      friends = dict(
          [(friend['screen_name'], friend['profile_image_url'])
              for friend in u_json])
      logging.debug('Retrievd %d friends of %s.' % (len(friends), self.username))
      return friends


def get(username):
  return User.get_by_key_name(username.lower())


def transaction_update_email(username, email):
  user = User.get_by_key_name(username.lower())
  user.email = email
  user.put()


def transaction_remove_email(username):
  user = User.get_by_key_name(username.lower())
  user.email = None
  user.last_mailed = None
  user.put()


def verify_twitter(username, password):
  headers = {
      'Authorization': 'Basic ' + base64.b64encode('%s:%s' % (username, password)),
      }
  f = urlfetch.fetch('https://twitter.com/account/verify_credentials.json', headers=headers)
  del password
  del headers
  return f.status_code == 200

def try_mail(u):
  if not u.last_updated or (datetime.datetime.utcnow() - u.last_updated).days > 0:
    # haven't updated, or data is too old
    return
  if u.email and (not u.last_mailed or (datetime.datetime.utcnow() - u.last_mailed).days > MAIL_INTERVAL):
    mail.send_mail(
        sender="support@example.com",
        to="%s <%s>" % (u.username, u.email),
        subject="Last Tweets",
        body="""
test mail
""")
  # TODO Update db
