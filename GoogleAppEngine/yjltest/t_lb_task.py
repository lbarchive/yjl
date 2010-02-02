import datetime as dt
import re

import simplejson as json

from google.appengine.api.urlfetch import fetch

from t_lb_model import TwitterLbRecord

SHOW_API = 'http://twitter.com/users/show/%s.json'


class ShowAPIError(Exception):

  pass


def t_lb_update():

  today = dt.datetime.utcnow()
 
  username = 'lyjl'
  
  f = fetch(SHOW_API % username)
  if f.status_code != 200:
    raise ShowAPIError('Failed to get user data: %d - %s' % (f.status_code, f.content))
  j = json.loads(f.content)
  
  td = today - dt.datetime.strptime(j['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
  tweets_per_day = j['statuses_count'] / (td.days + td.seconds / 86400.0)

  record = TwitterLbRecord(date=today, friends=j['friends_count'],
      followers=j['followers_count'], tweets=j['statuses_count'],
      tweets_per_day=tweets_per_day)
  record.put()
