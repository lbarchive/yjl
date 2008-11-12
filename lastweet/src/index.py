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
import os
import urllib

from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from lastweet import user, queue, util


class HomePage(webapp.RequestHandler):

  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    username = self.request.get('username')
    if username:
      self.redirect('/u/' + urllib.quote(username))
   
    template_values = {
      'messages': [['error', 'Please enter username']],
      }
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


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
          'messages': [],
          }
        pos = u._queued
        if pos:
          template_values['messages'].append(['message', 'This user is in queue #%d' % pos])
        if u.tweets:
          template_values['tweets'] = u._tweets_
      else:
        # the weets has been updated within 24 hours
        template_values = {
          'username': u.username,
          'profile_image': u.profile_image,
          'email': u.email,
          'last_mailed': u.last_mailed,
          'last_updated': u.last_updated,
          'messages': [],
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
          'email': u.email,
          'last_mailed': u.last_mailed,
          'messages': [['message', 'Put in queue #%d' % u._queued]],
          }
      elif u == 403:
        # Reject protected twitter user, can retrieve correct screen name and image from
        # friends list, but no need to waste a request to Twitter
        template_values = {
          'username': username,
          'profile_image': 'http://static.twitter.com/images/default_profile_normal.png',
          'messages': [['error', "This Twitter's tweets are protected."]],
          }
      elif u == 404:
        template_values = {
          'username': username,
          'profile_image': 'http://static.twitter.com/images/default_profile_normal.png',
          'messages': [['error', 'No such Twitter user']],
          }
      else:
        # Unknown error
        # FIXME use a real error page with status code for errors
        template_values = {
          'username': 'ERROR',
          'profile_image': 'http://static.twitter.com/images/default_profile_normal.png',
          'messages': [['error', 'Twitter responses with %d' % u]],
          }
    # Check if pinging system offline
    last_process = memcache.get('last_process_queue')
    if not last_process or util.td_seconds(last_process) > 600:
      template_values['messages'].append(['message', 'Pinging system is temporarily offine, you request will be processed in a few hours.'])

    path = os.path.join(os.path.dirname(__file__), 'template/user.html')
    self.response.out.write(template.render(path, template_values))


class SubscribePage(webapp.RequestHandler):
  """An interface to allow Twitter to subscribe via email"""

  def get_post_uri(self):
    post_uri = '/subscribe'
    server_name = os.environ.get('SERVER_NAME', '')
    if 'appspot.com' in server_name:
      post_uri = 'https://%s/subscribe' % server_name
    return post_uri

  def get(self):
    template_values = {
        'username': '',
        'email': '',
        'post_uri': self.get_post_uri(),
        'messages': '',
        }
    path = os.path.join(os.path.dirname(__file__), 'template/subscribe.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    email = self.request.get('email')

    template_values = {
        'username': username,
        'email': email,
        'post_uri': self.get_post_uri(),
        'messages': [],
        }

    if email:
      logging.debug('Checking email')
      # TODO is_email_valid not working on development and production servers
      if not mail.is_email_valid(email):
        template_values['messages'].append(['error', 'Email address is not valid'])
        path = os.path.join(os.path.dirname(__file__), 'template/subscribe.html')
        self.response.out.write(template.render(path, template_values))
        return

    if username and password:
      logging.debug('About to verify')
      if user.verify_twitter(username, password):
        # Make sure username in db
        u = user.get(username)
        if u is None:
          user.add(username)
        if email:
          db.run_in_transaction(user.transaction_update_email, username, email)
          template_values['messages'].append(['message', 'Email has been updated'])
        else:
          db.run_in_transaction(user.transaction_remove_email, username)
          template_values['messages'].append(['message', 'Email has been removed'])
      else:
        template_values['messages'].append(['error', 'Cannot verify Twitter account'])
      logging.debug('End of verifying')
    else:
      template_values['messages'].append(['error', 'Please input both username and password!'])
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
    self.response.out.write('Queue: %d\n' % status)


application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/about', AboutPage),
     (r'/u/(.*)', UserPage),
     ('/subscribe', SubscribePage),
     ('/ping', PingPage),
     ],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
