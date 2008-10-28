import cgi
import datetime
import logging
import pickle
import os

from google.appengine.api import urlfetch 
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json

from lastweet import user, queue


class HomePage(webapp.RequestHandler):
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


class CheckRedirection(webapp.RequestHandler):
  def post(self):
    self.redirect('/u/' + self.request.get('username'))


class UserPage(webapp.RequestHandler):
  def get(self, username):
    logging.debug('%s asked' % username)
    # Check if this username in db
    u = user.get(username)
    if u is not None:
      logging.debug('%s retrieved from db' % u.username)
      if u.last_updated is None or (datetime.datetime.utcnow() - u.last_updated).days > 0:
        # More than 24 hours or haven't updated
        queue.add(u)
        template_values = {
          'username': username,
          'profile_image': u.profile_image,
          'last_updated': u.last_updated,
          }
        if u._queued:
          template_values['messages'] = 'This user is in queue'
        if u.tweets:
          template_values['tweets'] = pickle.loads(u.tweets)
      else:
        # the weets has been updated within 24 hours
        # Also check if need to email result. mail is not empty and last_mail > 14 days
        template_values = {
          'username': username,
          'profile_image': u.profile_image,
          'last_updated': u.last_updated,
          'messages': '',
          'tweets': pickle.loads(u.tweets),
          }
    else:
      # This username isn't in db
      f = urlfetch.fetch('http://twitter.com/users/show/%s.json' % username)
      if f.status_code == 200:
        u_json = json.loads(f.content)
        if u_json['protected']:
          # Reject projected twitter user
          template_values = {
            'username': username,
            'messages': 'Protected',
            }
        else:
          # Create new entry
          u = user.User()
          u.username = username
          u.profile_image = u_json['profile_image_url']
          u.put()
          # Queue it
          queue.add(u)
          # Show page
          template_values = {
            'username': username,
            'profile_image': u.profile_image,
            'messages': 'Put in queue',
            }
    path = os.path.join(os.path.dirname(__file__), 'template/user.html')
    self.response.out.write(template.render(path, template_values))


class PingPage(webapp.RequestHandler):
  """Being pinged to process queue"""

  def get(self):
#    self.response.headers['Content-Type'] = 'text/plain'
    pinged = datetime.datetime.utcnow();
    self.response.out.write('Pinged at %s' % pinged)
    queue.process()
    diff = datetime.datetime.utcnow() - pinged
    seconds = diff.days * 86400 + diff.seconds + diff.microseconds / 1000000.0
    self.response.out.write(', took %f seconds.<BR>' % seconds)

    status = queue.get_status()
    self.response.out.write('Queue: %d, Remaining of Current: %d' % status)


application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/check', CheckRedirection),
     (r'/u/(.*)', UserPage),
     ('/ping', PingPage),
     ],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
