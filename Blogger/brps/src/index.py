# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
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


import simplejson as json
import logging
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from brps import post


def json_error(msg):
  error = {'error': msg}
  return json.dumps(error)


class HomePage(webapp.RequestHandler):

  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


class GetPage(webapp.RequestHandler):
  """Serves relates posts"""

  def get(self):
    blog_id = int(self.request.get('blog'))
    post_id = int(self.request.get('post'))
    callback = self.request.get('callback')
    if blog_id and post_id:
      p = post.get(blog_id, post_id)
      if not p:
        p = post.add(blog_id, post_id)
      json = p.relates
    else:
      # missing blog_id and/or post_id
      # http://www.iana.org/assignments/media-types/application/
      json = json_error('Missing Ids')
      return
    self.response.headers['Content-Type'] = 'application/json'
    if callback:
      self.response.out.write('%s(%s)' % (callback, json))
    else:
      self.response.out.write(json)


application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/get', GetPage),
     ],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
