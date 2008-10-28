import simplejson as json

from google.appengine.api import urlfetch 
from google.appengine.ext import db

from lastweet import queue


class User(db.Model):
  username = db.StringProperty()
  profile_image = db.StringProperty()
  email = db.StringProperty()
  last_mail = db.DateTimeProperty()
  last_update = db.DateTimeProperty()
  tweets = db.StringProperty()

  @property
  def _queued(self):
    return queue.has(self.username)

  @property
  def _friends(self):
    f = urlfetch.fetch('http://twitter.com/statuses/friends/%s.json' % self.username)
    if f.status_code == 200:
      u_json = json.loads(f.content)
      # TODO error
      friends = dict(
          [(friend['screen_name'], friend['profile_image_url'])
              for friend in u_json])
      return friends


def get(username):
  u = User.all()
  u.filter('username =', username)
  return u.get()
