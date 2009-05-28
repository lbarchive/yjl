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
URI_LATEST_POST = URI_BASE + 'viewtopic-p-%s.html#%s'
# Used to limit entries in new topics feed
MAX_ENTRIES = 50

#####
# REs

RE_SID = re.compile(r'\??sid=[0-9a-f]+')
RE_FORUM = re.compile(r'<a href="viewforum-f-(\d+)\.html" class="forumlink">(.*?)</a>')
RE_TOPIC = re.compile(r'<a href="viewtopic-t-(\d+)-highlight-\.html" class="topictitle">(.*?)</a>')
RE_REPLIES = re.compile(r'<td class="row2" align="center" valign="middle"><span class="postdetails">(\d+)</span></td>')
RE_AUTHOR_DATE = re.compile(r'<span class="postdetails">(.*?)<br /><a href="profile\.php.*?">(.*?)</a>')
RE_LATEST_POST = re.compile(r'<a href="viewtopic-p-(\d+)\.html#\1">.*?</a>')

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
      't_feed_uri': self.request.uri + 'forumsnewtopics',
      't_requests': s24.get_count('gentoo_forums_new_topics'),
      't_requests_chart': s24.get_chart_uri('gentoo_forums_new_topics', barcolor='006699'),
      }

    path = os.path.join(os.path.dirname(__file__), 'template/gentoo.html')
    self.response.out.write(template.render(path, template_values))


# New posts
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


class ForumsNewTopics(webapp.RequestHandler):

  def get(self):
    
    feed = memcache.get('gentoo_forums_new_topics_feed')

    if not feed:
      log.error('Data is not available')
      self.error(500)
      return

    self.response.headers.add_header('Content-Type', 'application/rss+xml')
    self.response.out.write(feed)

    s24.incr('gentoo_forums_new_topics')


class UpdateForumsFeed(webapp.RequestHandler):

  @staticmethod
  def _gen_feed(feed, entries):

    for entry in entries:
      feed.add_item(
          title='[%s] %s' % (entry['f_name'], entry['t_title']),
          link=URI_LATEST_POST % (entry['p_id'], entry['p_id']),
          description='',
          author_name=entry['author'],
          author_email='noreply@yjltest.appspot.com',
          pubdate=entry['date'],
          unique_id=URI_LATEST_POST % (entry['p_id'], entry['p_id']),
          categories=[entry['f_name']],
          )

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
    l_replies = 0
    l_author_date = 0
    l_latest_post = 0
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

      matches = RE_REPLIES.search(raw, l_replies)
      l_replies = matches.end() + 1
      replies = int(matches.groups()[0])

      matches = RE_AUTHOR_DATE.search(raw, l_author_date)
      l_author_date = matches.end() + 1
      date, author = matches.groups()
      date = datetime.strptime(date, '%a %b %d, %Y %I:%M %p').replace(tzinfo=local_tz).astimezone(utc)
      author = urllib.unquote(author)

      matches = RE_LATEST_POST.search(raw, l_latest_post)
      l_latest_post = matches.end() + 1
      post_id = matches.groups()[0]
      
      # Put them all together
      entries += [{'f_id': forum_id, 'f_name': forum_name, 't_id': topic_id,
          't_title': topic_title, 'date': date, 'author': author,
          'p_id': post_id, 'replies': replies}]

    if not entries:
      # Got thing!?
      log.error('Found nothing in last 24 hours page')
      self.error(500)
      return
    
    # Generating the new posts feed
    feed = fg.Rss201rev2Feed(
        title='Gentoo Forums: Lastest posts',
        description='Unofficial feed of Gentoo Forums New Posts',
        link=L24_URI,
        feed_url='http://yjltest.appspot.com/gentoo/forumsfeed',
        )
    self._gen_feed(feed, entries)
    memcache.set('gentoo_forums_l24_feed', feed.writeString('utf-8'))

    # Generating the new topics feed
    # new_topics: newest to older
    new_topics = memcache.get('gentoo_forums_new_topics')
    if new_topics is None:
      new_topics = []

    # Checking if entries are new, stop at first repeating entry in new_topics
    new_entries = []
    for entry in entries:
      if new_topics and entry['t_id'] == new_topics[0]['t_id']:
        break
      # FIXME New topic? replies may not be 100% precise to decide, views? It's
      # possible to have at least one reply within 10 minutes.
      if entry['replies'] > 0:
        continue
      log.debug('%s: %d' % (entry['t_title'], entry['replies']))
      new_entries += [entry]

    # Merge into new_topics, and truncat
    new_topics = (new_entries + new_topics)[:MAX_ENTRIES]
    del new_entries
    memcache.set('gentoo_forums_new_topics', new_topics)
    log.debug(repr(new_topics))
    feed = fg.Rss201rev2Feed(
        title='Gentoo Forums: New topics',
        description='Unofficial feed of Gentoo Forums New Topics',
        link='http://forums.gentoo.org/',
        feed_url='http://yjltest.appspot.com/gentoo/forumsnewtopics',
        )
    self._gen_feed(feed, new_topics)
    memcache.set('gentoo_forums_new_topics_feed', feed.writeString('utf-8'))
 
    self.response.out.write('Feeds generated successfully.')


application = webapp.WSGIApplication([
    ('/gentoo/', HomePage),
    ('/gentoo/forumsfeed', ForumsFeed),
    ('/gentoo/forumsnewtopics', ForumsNewTopics),
    ('/gentoo/updateforumsfeed', UpdateForumsFeed),
    ],
    debug=True)
    

def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
