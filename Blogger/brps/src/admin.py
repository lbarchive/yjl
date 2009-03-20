# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
# Copyright (C) 2009  Yu-Jie Lin
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


"""Admin interface"""


import os

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import config
from brps import post, util
import Simple24


class AdminPage(webapp.RequestHandler):

  def get(self):
    """Get method handler"""
    blogs = (memcache.get('blogs') or {}).values()
    blogs.sort()
    template_values = {
      'completed_requests': Simple24.get_count('completed_requests'),
      'chart_uri': Simple24.get_chart_uri('completed_requests'),
      'blogs': blogs,
      'blogs_reset': memcache.get('blogs_reset'),
      'before_head_end': config.before_head_end,
      'after_footer': config.after_footer,
      'before_body_end': config.before_body_end,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/admin.html')
    self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
    [('/admin', AdminPage),
     ],
    debug=True)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
