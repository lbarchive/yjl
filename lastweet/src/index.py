import cgi
import datetime
import simplejson as json
import logging
import os
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from lastweet import user, queue


class HomePage(webapp.RequestHandler):
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


class CheckRedirection(webapp.RequestHandler):
  def post(self):
    self.redirect('/u/' + urllib.quote(self.request.get('username')))


class UserPage(webapp.RequestHandler):
  def get(self, username):
    logging.debug('%s asked' % username)
    # Check if this username in db
    u = user.get(username)
    if u is not None:
      logging.debug('%s retrieved from db' % u.username)
      if u._need_update:
        # More than 24 hours or haven't updated
        queue.add(u)
        template_values = {
          'username': u.username,
          'profile_image': u.profile_image,
          'last_updated': u.last_updated,
          }
        pos = u._queued
        if pos:
          template_values['messages'] = 'This user is in queue #%d' % pos
        if u.tweets:
          template_values['tweets'] = u._tweets_
      else:
        # the weets has been updated within 24 hours
        # Also check if need to email result. mail is not empty and last_mail > 14 days
        template_values = {
          'username': u.username,
          'profile_image': u.profile_image,
          'last_updated': u.last_updated,
          'messages': '',
          'tweets': u._tweets_,
          }
    else:
      # This username isn't in db, trying to add
      u = user.add(username)
      if isinstance(u, user.User):
        # Show page
        template_values = {
          'username': u.username,
          'profile_image': u.profile_image,
          'messages': 'Put in queue #%d' % u._queued,
          }
      elif u == 403:
        # Reject protected twitter user, can retrieve correct screen name and image from
        # friends list, but no need to waste a request to Twitter
        template_values = {
          'username': username,
          'profile_image': 'http://static.twitter.com/images/default_profile_normal.png',
          'messages': "This Twitter's tweets are protected.",
          }
      elif u == 404:
        template_values = {
          'username': username,
          'profile_image': 'http://static.twitter.com/images/default_profile_normal.png',
          'messages': 'No such Twitter user',
          }
      else:
        # Unknown error
        # FIXME use a real error page with status code for errors
        template_values = {
          'username': 'ERROR',
          'profile_image': 'http://static.twitter.com/images/default_profile_normal.png',
          'messages': 'Twitter responses with %d' % u,
          }

    path = os.path.join(os.path.dirname(__file__), 'template/user.html')
    self.response.out.write(template.render(path, template_values))


class SubscribePage(webapp.RequestHandler):
  """An interface to allow Twitter to subscribe via email"""

  def get(self):
    template_values = {
        'username': '',
        'email': '',
        'messages': '',
        }
    path = os.path.join(os.path.dirname(__file__), 'template/subscribe.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    email = self.request.get('email')
    # TODO check user
    # TODO mail.is_email_valid
    if username and password:
      if user.verify_twitter(username, password):
        template_values = {
            'username': username,
            'email': email,
            }
        if email:
          db.run_in_transaction(user.transaction_update_email, username, email)
          template_values['messages'] = 'Updated'
        else:
          db.run_in_transaction(user.transaction_remove_email, username)
          template_values['messages'] = 'Removed'
      else:
        template_values = {
            'username': username,
            'email': email,
            'messages': 'NO',
            }
    else:
      template_values = {
          'username': username,
          'email': email,
          'messages': 'Please input both username and password!',
          }
    del password

    path = os.path.join(os.path.dirname(__file__), 'template/subscribe.html')
    self.response.out.write(template.render(path, template_values))


class AboutPage(webapp.RequestHandler):
  """Serves about page"""

  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'template/about.html')
    self.response.out.write(template.render(path, template_values))


class PingPage(webapp.RequestHandler):
  """Being pinged to process queue"""

  def get(self):
    pinged = datetime.datetime.utcnow();
    self.response.out.write('Pinged at %s' % pinged)
    queue.process()
    diff = datetime.datetime.utcnow() - pinged
    seconds = diff.days * 86400 + diff.seconds + diff.microseconds / 1000000.0
    self.response.out.write(', took %f seconds.<BR>' % seconds)

    status = queue.get_status()
    self.response.out.write('Queue: %d' % status)


application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/about', AboutPage),
     ('/check', CheckRedirection),
     (r'/u/(.*)', UserPage),
     ('/subscribe', SubscribePage),
     ('/ping', PingPage),
     ],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
