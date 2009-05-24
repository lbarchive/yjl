# Copyright (c) 2009, Yu-Jie Lin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the organization nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY Yu-Jie Lin ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Yu-Jie Lin BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# This script scrapes Gentoo Forums' last 24 hours page:
#   http://forums.gentoo.org/search.php?search_id=last
# And convert it into a feed. It caches for 10 minutes.


from datetime import datetime, timedelta, tzinfo
import logging as log
import os
import re
import time
import urllib

from google.appengine.api import memcache
from google.appengine.api.urlfetch import DownloadError, fetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import feedgenerator as fg

import Simple24 as s24


URI_BASE = 'http://forums.gentoo.org/'
L24_URI = URI_BASE + 'search.php?search_id=last'
CACHE_TIME = 60 * 10
URI_TOPIC = URI_BASE + 'viewtopic-t-%s-highlight-.html'

#####
# REs

RE_SID = re.compile('\??sid=[0-9a-f]+')
RE_FORUM = re.compile('<a href="viewforum-f-(\d+)\.html" class="forumlink">(.*?)</a>')
RE_TOPIC = re.compile('<a href="viewtopic-t-(\d+)-highlight-\.html" class="topictitle">(.*?)</a>')
RE_AUTHOR_DATE = re.compile('<span class="postdetails">(.*?)<br /><a href="profile\.php.*?">(.*?)</a>')

##########
# Timezone

ZERO = timedelta(0)
class UTC(tzinfo):

  def utcoffset(self, dt):
    return ZERO

  def tzname(self, dt):
    return "UTC"

  def dst(self, dt):
    return ZERO

# Local time on Gentoo Forums
# All GAE servers are in USA, right?
if 'Development' in os.environ.get('SERVER_SOFTWARE', ''):
  time.daylight = 1
# May have problem when DST switches because module is cached
if time.daylight:
  LOCAL_UTC_OFFSET = timedelta(seconds=-5*3600)
else:
  LOCAL_UTC_OFFSET = timedelta(seconds=-6*3600)
LOCAL_DST = timedelta(seconds=+1 * 3600)
class LOCAL_TZ(tzinfo):

  def utcoffset(self, dt):
    return LOCAL_UTC_OFFSET

  def tzname(self, dt):
    if time.daylight:
      return "CDT"
    else:
      return "CT"

  def dst(self, dt):
    if time.daylight:
      return LOCAL_DST
    else:
      return ZERO

utc = UTC()
local_tz = LOCAL_TZ()

##########
# Handlers

class HomePage(webapp.RequestHandler):

  def get(self):
    
    template_values = {
      'title': 'Stuff for Gentoo',
      'feed_uri': self.request.uri + 'forumsfeed',
      'requests': s24.get_count('gentoo_forums_l24_feed'),
      'requests_chart': s24.get_chart_uri('gentoo_forums_l24_feed', barcolor='006699'),
      }

    path = os.path.join(os.path.dirname(__file__), 'template/gentoo.html')
    self.response.out.write(template.render(path, template_values))


class ForumsFeed(webapp.RequestHandler):

  def get(self):
    
    feed = memcache.get('gentoo_forums_l24_feed')

    if not feed:
      log.error('Data is not available')
      self.error(500)
      return

    self.response.headers.add_header('Content-Type', 'application/rss+xml')
    self.response.out.write(feed)

    s24.incr('gentoo_forums_l24_feed')


class UpdateForumsFeed(webapp.RequestHandler):

  def get(self):

    # TODO: Check if it is time to update
    # Currently using cron, so just believe that. What I can say? I am lazy!

    try:
      resp = fetch(L24_URI)
      if resp.status_code != 200:
        log.error('Error on fetching L24 page')
        self.error(500)
        return
      raw = resp.content
      raw = RE_SID.sub('', raw)
      del resp
    except DownloadError:
      log.error('Download error on fetching L24 page')
      self.error(500)
      return

    entries = []
    l_forum = 0
    l_topic = 0
    l_author_date = 0
    while True:
      matches = RE_FORUM.search(raw, l_forum)
      if not matches:
        # Should be finished
        break
      l_forum = matches.end() + 1
      forum_id, forum_name = matches.groups()
      forum_name = urllib.unquote(forum_name)

      matches = RE_TOPIC.search(raw, l_topic)
      l_topic = matches.end() + 1
      topic_id, topic_title = matches.groups()
      topic_title = urllib.unquote(topic_title)

      matches = RE_AUTHOR_DATE.search(raw, l_author_date)
      l_author_date = matches.end() + 1
      date, author = matches.groups()
      date = datetime.strptime(date, '%a %b %d, %Y %I:%M %p').replace(tzinfo=local_tz).astimezone(utc)
      author = urllib.unquote(author)

      # Put them all together
      entries += [(forum_id, forum_name, topic_id, topic_title, date, author)]

    if not entries:
      # Got thing!?
      log.error('Found nothing in last 24 hours page')
      self.error(500)
      return

    # Memcache the list
    #memcache.set('gentoo_forums_l24', entries)
    #memcache.set('gentoo_forums_l24_updated', time.time())

    # Generating the feed
    feed = fg.Rss201rev2Feed(
        title='Gentoo Forums: Lastest',
        description='Unofficial feed of Gentoo Forums',
        link=L24_URI,
        feed_url=self.request.uri,
        )

    for entry in entries:
      feed.add_item(
          title='[%s] %s' % (entry[1], entry[3]),
          link=URI_TOPIC % entry[2],
          description='',
          author_name=entry[5],
          author_email='noreply@yjltest.appspot.com',
          pubdate=entry[4],
          unique_id=URI_TOPIC % entry[2],
          categories=[entry[1]],
          )

    raw_feed = feed.writeString('utf8')
    memcache.set('gentoo_forums_l24_feed', raw_feed)
    # GAE already handles this
    # memcache.set('gentoo_forums_l24_feed_gzip', zlib.compress(raw_feed))


application = webapp.WSGIApplication([
    ('/gentoo/', HomePage),
    ('/gentoo/forumsfeed', ForumsFeed),
    ('/gentoo/updateforumsfeed', UpdateForumsFeed),
    ],
    debug=True)
    

def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
