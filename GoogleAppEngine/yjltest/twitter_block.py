# Author: Yu-Jie Lin
# This code is put into Public Domain
import base64
import logging
import os

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json


def fetch(uri, username='', password='', **kws):
  # Can fetch with Basic Authentication
  headers = {}
  if username and password:
    headers['Authorization'] = 'Basic ' + base64.b64encode('%s:%s' % (username, password))

  f = urlfetch.fetch(uri, headers=headers, **kws)
  logging.debug('Fetching %s (%s): %d' % (uri, username, f.status_code))
  return f


class HomePage(webapp.RequestHandler):

  def get(self):

    tmpl_values = {
        }
    path = os.path.join(os.path.dirname(__file__), 'template/twitter_block.html')
    self.response.out.write(template.render(path, tmpl_values))

  def post(self):

    twitter_id = self.request.get('twitter_id', '')
    twitter_pw = self.request.get('twitter_pw', '')
    page = self.request.get('page', 1)

    tmpl_values = {
        'twitter_id': twitter_id,
        'twitter_pw': twitter_pw,
        'post': True,
        }
    # Verify account
    f = fetch('https://twitter.com/account/verify_credentials.json', twitter_id, twitter_pw)
    if f.status_code == 200:
      # Check cache
      rendered_page = memcache.get(twitter_id, namespace='twitter_blocklist')
      if rendered_page:
        self.response.out.write(rendered_page)
        return
      try:
        # XXX the page didn't work, Twitter still return whole list
        f = fetch('https://twitter.com/blocks/blocking.json?page=' + page, twitter_id, twitter_pw, deadline=10)
        if f.status_code == 200:
          lst = json.loads(f.content)
          tmpl_values['blocks'] = lst
        else:
          tmpl_values['error'] = 'Unable to retrieve list, got %d from Twitter: %s' % (f.status_code, f.content)
      except urlfetch.DownloadError, e:
        tmpl_values['error'] = e.message
    else:
      tmpl_values['error'] = 'ID and/or PW is wrong!'
    path = os.path.join(os.path.dirname(__file__), 'template/twitter_block.html')
    rendered_page = template.render(path, tmpl_values)
    self.response.out.write(rendered_page)
    if 'error' not in tmpl_values:
      memcache.set(twitter_id, rendered_page, 3600, namespace='twitter_blocklist')
  def head(self):

    pass


application = webapp.WSGIApplication([
    ('/twitter_blocklist', HomePage),
    ],
    debug=True)


def main():
  
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
