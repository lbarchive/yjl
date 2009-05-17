#!/usr/bin/python


from datetime import datetime, timedelta, tzinfo
import sys
import time

import friendfeed as ff
import twitter

import clis_cfg as cfg

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

utc = UTC()


class LOCAL_TZ(tzinfo):

  def utcoffset(self, dt):
    return timedelta(seconds=-1*time.altzone)

  def tzname(self, dt):
    return "UTC"

  def dst(self, dt):
    # FIXME not sure if it is in seconds
    return timedelta(seconds=-1*time.daylight)

local_tz = LOCAL_TZ()

##############
# Source class

class Source(object):
  pass


class Twitter(Source):

  def __init__(self, src):
    
    self.last_accessed = 0
    self.since_id = None
    self.api = twitter.Api(username=src['username'], password=src['password'])
    if 'interval' in src:
      self.interval = src['interval']
    else:
      self.interval = 60
    if 'output' in src:
      self.output = src['output']
    if 'date_fmt' in src:
      self.date_fmt = src['date_fmt']

  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return

#    msg = 'Accessing...'
#    print msg,
#    sys.stdout.flush()
    if self.since_id:
      statuses = self.api.GetFriendsTimeline(since_id=self.since_id)
    else:
      statuses = self.api.GetFriendsTimeline()
#    print '\x08' * (len(msg) + 2),
#    sys.stdout.flush()
#    print '\x0d' + ' ' * int(os.environ['COLUMNS'])
    if statuses:
      self.since_id = statuses[0].id
    statuses.reverse()
    for status in statuses:
      d = status.AsDict()
#      print d
      d['created_at'] = datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      d['url'] = 'http://twitter.com/%s/status/%d' % (status.user.screen_name, status.id)
      #d['created_at'] = datetime.strptime(status.created_at, '%a %b %d %H:%M:%S %z %Y').strftime(self.date_fmt)
      d['user_screen_name'] = status.user.screen_name
      print self.output % d
    self.last_accessed = time.time()


class FriendFeed(Source):

  def __init__(self, src):

    self.last_accessed = 0
    self.token = None
    self.api = ff.FriendFeed(src['nickname'], src['remote_key'])
    if 'interval' in src:
      self.interval = src['interval']
    else:
      self.interval = 60
    if 'output' in src:
      self.output = src['output']
    if 'output_like' in src:
      self.output_like = src['output_like']
    if 'output_comment' in src:
      self.output_comment = src['output_comment']
    if 'date_fmt' in src:
      self.date_fmt = src['date_fmt']

  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return

    if not self.token:
      self.token = self.api.fetch_updates()['update']['token']

    home = self.api.fetch_updates_home(token=self.token, timeout=0)
    self.token = home['update']['token']

    entries = home['entries']
    for entry in entries:
      entry['user_nickname'] = entry['user']['nickname']
      entry['updated'] = entry['updated'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      entry['entry_link'] = 'http://friendfeed.com/e/%s' % entry['id']
      if 'room' in entry:
        entry['room'] = entry['room']['name']
      else:
        entry['room'] = ''

      if entry['is_new']:
        print self.output % entry
      for like in entry['likes']:
        if like['is_new']:
          like['user_nickname'] = like['user']['nickname']
          like['date'] = like['date'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
          like['title'] = entry['title']
          like['entry_link'] = entry['entry_link']
          print self.output_like % like
      for comment in entry['comments']:
        if comment['is_new']:
          comment['user_nickname'] = comment['user']['nickname']
          comment['date'] = comment['date'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
          comment['title'] = entry['title']
          comment['entry_link'] = entry['entry_link']
          print self.output_comment % comment

SOURCE_CLASSES = {'twitter': Twitter, 'friendfeed': FriendFeed}


sources = []
for src in cfg.sources:
  if 'type' not in src:
    print 'ERROR: Source type unspecified: %s' % repr(src)
    continue
  if src['type'] in SOURCE_CLASSES:
    sources.append(SOURCE_CLASSES[src['type']](src))
  else:
    print 'ERROR: Unknown source type: %s' % src['type']


while True:
  for src in sources:
    src.update()
  time.sleep(1)
