# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
# Copyright (C) 2008, 2009  Yu-Jie Lin
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


from datetime import timedelta
import simplejson as json
import StringIO
import logging
import os

from google.appengine.api import memcache
from google.appengine.api.urlfetch import DownloadError, fetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError 
try:
  # When deployed
  from google.appengine.runtime import DeadlineExceededError
except ImportError:
  # In the development server
  from google.appengine.runtime.apiproxy_errors import DeadlineExceededError

import config
from brps import post, util
import Simple24


def send_json(response, obj, callback):
  json_result = obj
  if not isinstance(obj, (str, unicode)):
    json_result = json.dumps(obj)

  response.headers['Content-Type'] = 'application/json'
  if callback:
    response.out.write('%s(%s)' % (callback, json_result))
  else:
    response.out.write(json_result)


def json_error(response, code, msg, callback):
  # 1 - Missing Ids
  # 2 - GAE problem
  # 3 - Server is processing, try again
  # 99 - Unknown problem
  # TODO sends 500
  send_json(response, {'code': code, 'error': msg}, callback)


class HomePage(webapp.RequestHandler):

  def get(self):
    template_values = {
      'after_footer': config.after_footer,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


class StatsPage(webapp.RequestHandler):
  """Statistics Page"""

  def get(self):
    blogs = (memcache.get('blogs') or {}).values()
    blogs.sort()
    template_values = {
      'completed_requests': Simple24.get_count('completed_requests'),
      'chart_uri': Simple24.get_chart_uri('completed_requests'),
      'blogs': blogs,
      'blogs_reset': memcache.get('blogs_reset'),
      'after_footer': config.after_footer,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/stats.html')
    self.response.out.write(template.render(path, template_values))


class GetPage(webapp.RequestHandler):
  """Serves relates posts"""

  def get(self):
    callback = self.request.get('callback')
    try:
      blog_id = int(self.request.get('blog'))
      post_id = int(self.request.get('post'))
    except ValueError:
      json_error(self.response, 1, 'Missing Ids', callback)
      return

    try:
      p = post.get(blog_id, post_id)
      if not p:
        try:
          p = post.add(blog_id, post_id)
        except CapabilityDisabledError:
          logging.debug('Caught CapabilityDisabledError')
          json_error(self.response, 2, 'Unable to process, Google App Engine may be under maintenance.', callback)
          return
      if p:
        send_json(self.response, p.relates, callback)
        Simple24.incr('completed_requests')
        # Add to blog list
        blogs = memcache.get('blogs')
        blogs_reset = memcache.get('blogs_reset')
        if blogs is None or blogs_reset is None:
          blogs = {}
          memcache.set('blogs', blogs)
          memcache.set('blogs_reset', util.now() + timedelta(days=1), 86400)
        if blog_id not in blogs:
          try:
            f = fetch('http://www.blogger.com/feeds/%s/posts/default?v=2&alt=json&max-results=0' % blog_id)
            if f.status_code == 200:
              p_json = json.loads(f.content.replace('\t', '\\t'))
              blog_name = p_json['feed']['title']['$t']
              blog_uri = ''
              for link in p_json['feed']['link']:
                if link['rel'] == 'alternate' and link['type'] == 'text/html':
                  blog_uri = link['href']
                  break
              blogs[blog_id] = (blog_name, blog_uri)
              memcache.set('blogs', blogs)
            else:
              logging.warning('Unable to fetch blog info %s, %d.' % (blog_id, f.status_code))
          except Exception, e:
            logging.warning('Unable to add blog %s, %s: %s' % (blog_id, type(e), e))
      else:
        json_error(self.response, 99, 'Unable to get related posts', callback)
    except (DownloadError, DeadlineExceededError):
      # Should be a timeout, just tell client to retry in a few seconds
      json_error(self.response, 3, '<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> is processing for this post... will retry in a few seconds...', callback)


application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/stats', StatsPage),
     ('/get', GetPage),
     ],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
