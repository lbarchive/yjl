import logging
import simplejson as json

from google.appengine.api import urlfetch 
from google.appengine.ext import db

from lastweet import queue


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
  u = User.all()
  u.filter('username =', username)
  return u.get()
