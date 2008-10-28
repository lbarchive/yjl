import cgi
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
    # Check if this username in db
    u = user.get(username)
    if u is not None:
      # Check if this username is in queue
      if u._queued:
        # Queued, so show old tweets for now
        pass
      elif u.last_update: #TODO
        # Queue this username if more than 24 hours
        pass
      else:
        # the weets has been updated within 24 hours
        # Also check if need to email result. mail is not empty and last_mail > 14 days
        pass
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
          path = os.path.join(os.path.dirname(__file__), 'template/user.html')
          self.response.out.write(template.render(path, template_values))
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
            'messages': 'Put in queue',
            }
          path = os.path.join(os.path.dirname(__file__), 'template/user.html')
          self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/check', CheckRedirection),
     (r'/u/(.*)', UserPage),
     ],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
