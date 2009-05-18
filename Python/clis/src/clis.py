#!/usr/bin/python
# GPLv3
# References
# http://code.google.com/p/python-twitter/
# http://code.google.com/p/friendfeed-api/
# http://feedparser.org/
# Todo
# TODO Store session data
# TODO flatten dict or a better templating

from datetime import datetime, timedelta, tzinfo
import sys
import time
import urllib
import urllib2

import feedparser as fp
import friendfeed as ff
import twitter

import clis_cfg as cfg

###########
# Utilities

def p(msg):

  sys.stdout.write(msg)
  sys.stdout.flush()


def p_clr(msg):

  sys.stdout.write('\x0d' + ' ' * len(msg) + '\x0d')
  sys.stdout.flush()


##################
# ANSI escape code

ANSI = {
    # http://en.wikipedia.org/wiki/ANSI_escape_code
    'ansi_reset': '\033[0m',
    'ansi_bold': '\033[1m',
    'ansi_underline': '\033[4m',
    'ansi_blink': '\033[5m',
    'ansi_no_underline': '\033[24m',
    'ansi_no_blink': '\033[25m',
    'ansi_fblack': '\033[30m',
    'ansi_fred': '\033[31m',
    'ansi_fgreen': '\033[32m',
    'ansi_fyellow': '\033[33m',
    'ansi_fblue': '\033[34m',
    'ansi_fmagenta': '\033[35m',
    'ansi_fcyan': '\033[36m',
    'ansi_fwhite': '\033[37m',
    'ansi_freset': '\033[39m',
    'ansi_bblack': '\033[40m',
    'ansi_bred': '\033[41m',
    'ansi_bgreen': '\033[42m',
    'ansi_byellow': '\033[43m',
    'ansi_bblue': '\033[44m',
    'ansi_bmagenta': '\033[45m',
    'ansi_bcyan': '\033[46m',
    'ansi_bwhite': '\033[47m',
    'ansi_breset': '\033[49m',
    'ansi_fiblack': '\033[90m',
    'ansi_fired': '\033[91m',
    'ansi_figreen': '\033[92m',
    'ansi_fiyellow': '\033[93m',
    'ansi_fiblue': '\033[94m',
    'ansi_fimagenta': '\033[95m',
    'ansi_ficyan': '\033[96m',
    'ansi_fiwhite': '\033[97m',
    'ansi_biblack': '\033[100m',
    'ansi_bired': '\033[101m',
    'ansi_bigreen': '\033[102m',
    'ansi_biyellow': '\033[103m',
    'ansi_biblue': '\033[104m',
    'ansi_bimagenta': '\033[105m',
    'ansi_bicyan': '\033[106m',
    'ansi_biwhite': '\033[107m',
    }

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


class LOCAL_TZ(tzinfo):

  def utcoffset(self, dt):
    return timedelta(seconds=-1*time.altzone)

  def tzname(self, dt):
    return "UTC"

  def dst(self, dt):
    # FIXME not sure if it is in seconds
    return timedelta(seconds=-1*time.daylight)


utc = UTC()
local_tz = LOCAL_TZ()

##############
# Source class

class Source(object):
  pass


class Twitter(Source):

  def __init__(self, src):
    
    self.last_accessed = 0
    self.username = src['username']
    self.api = twitter.Api(username=self.username, password=src['password'])
    # Get the latest id
    self.since_id = self.api.GetPublicTimeline()[0].id
    self.src_name = src.get('src_name', 'Tw')
    self.interval = src.get('interval', 60)
    if 'output' in src:
      self.output = src['output']
    if 'date_fmt' in src:
      self.date_fmt = src['date_fmt']

  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = '%sAccessing [%s] %s...%s' % (ANSI['ansi_fired'], self.src_name, self.username, ANSI['ansi_freset'])
    p(msg)
    if self.since_id:
      statuses = self.api.GetFriendsTimeline(since_id=self.since_id)
    else:
      statuses = self.api.GetFriendsTimeline()
    p_clr(msg)
    if statuses:
      self.since_id = statuses[0].id
    statuses.reverse()
    for status in statuses:
      d = status.AsDict()
      # FIXME
      d['created_at'] = datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      d['link'] = 'http://twitter.com/%s/status/%d' % (status.user.screen_name, status.id)
      #d['created_at'] = datetime.strptime(status.created_at, '%a %b %d %H:%M:%S %z %Y').strftime(self.date_fmt)
      d['user_screen_name'] = status.user.screen_name
      # FIXME
      d.update(ANSI)
      d.update(src_name=self.src_name)
      print self.output % d


class FriendFeed(Source):

  def __init__(self, src):

    self.last_accessed = 0
    self.token = None
    self.nickname = src['nickname']
    self.api = ff.FriendFeed(self.nickname, src['remote_key'])
    self.src_name = src.get('src_name', 'FF')
    self.interval = src.get('interval', 60)
    if 'output' in src:
      self.output = src['output']
    if 'output_like' in src:
      self.output_like = src['output_like']
    if 'output_comment' in src:
      self.output_comment = src['output_comment']
    self.show_like = src.get('show_like', True)
    self.show_comment = src.get('show_comment', True)
    if 'date_fmt' in src:
      self.date_fmt = src['date_fmt']

  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    if not self.token:
      self.token = self.api.fetch_updates()['update']['token']

    msg = '%sAccessing [%s] %s...%s' % (ANSI['ansi_fired'], self.src_name, self.nickname, ANSI['ansi_freset'])
    #msg = 'Accessing [%s] %s...' % (self.src_name, self.nickname)
    p(msg)
    home = self.api.fetch_updates_home(token=self.token, timeout=0)
    p_clr(msg)
    self.token = home['update']['token']

    entries = home['entries']
    for entry in entries:
      entry['user_nickname'] = entry['user']['nickname']
      # FIXME
      entry['updated'] = entry['updated'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      entry['entry_link'] = 'http://friendfeed.com/e/%s' % entry['id']
      if 'room' in entry:
        entry['room'] = '[%s]' % entry['room']['name']
      else:
        entry['room'] = ''

      if entry['is_new']:
        # FIXME
        entry.update(ANSI)
        entry.update(src_name=self.src_name)
        print self.output % entry

      if self.show_like:
        for like in entry['likes']:
          if like['is_new']:
            like['user_nickname'] = like['user']['nickname']
            # FIXME
            like['date'] = like['date'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
            like['title'] = entry['title']
            like['entry_link'] = entry['entry_link']
            # FIXME
            like.update(ANSI)
            like.update(src_name=self.src_name)
            print self.output_like % like

      if self.show_comment:
        for comment in entry['comments']:
          if comment['is_new']:
            comment['user_nickname'] = comment['user']['nickname']
            # FIXME
            comment['date'] = comment['date'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
            comment['title'] = entry['title']
            comment['entry_link'] = entry['entry_link']
            # FIXME
            comment.update(ANSI)
            comment.update(src_name=self.src_name)
            print self.output_comment % comment


class Feed(Source):

  def __init__(self, src):
    
    self.last_accessed = 0
    #self.username = src['username']
    #self.api = twitter.Api(username=self.username, password=src['password'])
    self.feed = src['feed']
    # Get the latest id
    try:
      self.last_id = fp.parse(self.feed).entries[0].id
    except:
      self.last_id = None
    self.src_name = src.get('src_name', 'Fd')
    self.interval = src.get('interval', 60)
    if 'output' in src:
      self.output = src['output']
    if 'date_fmt' in src:
      self.date_fmt = src['date_fmt']

  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = '%sAccessing [%s] %s...%s' % (ANSI['ansi_fired'], self.src_name, self.feed, ANSI['ansi_freset'])
    p(msg)
    feed = fp.parse(self.feed)
    p_clr(msg)
    entries = []
    if feed['entries']:
      # Get entries after last_id
      for entry in feed['entries']:
        if entry['id'] == self.last_id:
          break
        entries += [entry]
    # Update last_id
    if entries:
      self.last_id = entries[0]['id']

    entries.reverse()
    for entry in entries:
      # FIXME
      entry['updated'] = datetime.strptime(entry['updated'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      # FIXME
      entry.update(ANSI)
      entry.update(src_name=self.src_name)
      print self.output % entry


# http://stackoverflow.com/questions/52880/google-reader-api-unread-count
class GoogleBase(Source):

  def __init__(self, src):

    auth_url = 'https://www.google.com/accounts/ClientLogin'
    self.email = src['email']
    auth_req_data = urllib.urlencode({'Email': self.email,
                                      'Passwd': src['password']})
    auth_req = urllib2.Request(auth_url, data=auth_req_data)
    auth_resp = urllib2.urlopen(auth_req)
    auth_resp_content = auth_resp.read()
    auth_resp_dict = dict(x.split('=') for x in auth_resp_content.split('\n') if x)
    self.SID = auth_resp_dict["SID"]

  def get(self, url, header=None):

    if header is None:
      header = {}

    header['Cookie'] = 'Name=SID;SID=%s;Domain=.google.com;Path=/;Expires=160000000000' % self.SID

    req = urllib2.Request(url, None, header)
    f = urllib2.urlopen(req)
    content = f.read()
    f.close()
    return content


class GoogleMail(Source):

  def __init__(self, src):
    
    self.last_accessed = 0
    self.email = src['email']
    self.password = src['password']
    try:
      self.last_id = self.get_list().entries[0].id
    except:
      self.last_id = None
    self.src_name = src.get('src_name', 'GM')
    self.interval = src.get('interval', 60)
    if 'output' in src:
      self.output = src['output']
    if 'date_fmt' in src:
      self.date_fmt = src['date_fmt']

  def get_list(self):

    # FIXME Check if we can use ClientLogin, don't like password being stored
    feed = fp.parse('https://%s:%s@mail.google.com/mail/feed/atom' % (urllib.quote(self.email), urllib.quote(self.password)))
    return feed

  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = '%sAccessing [%s] %s...%s' % (ANSI['ansi_fired'], self.src_name, self.email, ANSI['ansi_freset'])
    p(msg)
    feed = self.get_list()
    p_clr(msg)
    entries = []
    if feed['entries']:
      # Get entries after last_id
      for entry in feed['entries']:
        if entry['id'] == self.last_id:
          break
        entries += [entry]
    # Update last_id
    if entries:
      self.last_id = entries[0]['id']

    entries.reverse()
    for entry in entries:
      entry['author_name'] = entry['author']#['name']
      # FIXME
      entry['updated'] = datetime.strptime(entry['updated'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      # FIXME
      entry.update(ANSI)
      entry.update(src_name=self.src_name)
      print self.output % entry


class GoogleReader(GoogleBase):

  def __init__(self, src):
    
    GoogleBase.__init__(self, src)

    self.last_accessed = 0
    
    try:
      self.last_id = self.get_list().entries[0].id
    except:
      self.last_id = None
    self.src_name = src.get('src_name', 'GR')
    self.interval = src.get('interval', 60)
    if 'output' in src:
      self.output = src['output']
    if 'date_fmt' in src:
      self.date_fmt = src['date_fmt']

  def get_list(self):

    content = self.get('http://www.google.com/reader/atom/user%2F-%2Fstate%2Fcom.google%2Freading-list')
    return fp.parse(content)

  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = '%sAccessing [%s] %s...%s' % (ANSI['ansi_fired'], self.src_name, self.email, ANSI['ansi_freset'])
    p(msg)
    feed = self.get_list()
    p_clr(msg)
    entries = []
    if feed['entries']:
      # Get entries after last_id
      for entry in feed['entries']:
        if entry['id'] == self.last_id:
          break
        entries += [entry]
    # Update last_id
    if entries:
      self.last_id = entries[0]['id']

    entries.reverse()
    for entry in entries:
      entry['source_title'] = entry['source']['title']
      # FIXME
      entry['updated'] = datetime.strptime(entry['updated'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      # FIXME
      entry.update(ANSI)
      entry.update(src_name=self.src_name)
      print self.output % entry


SOURCE_CLASSES = {'twitter': Twitter, 'friendfeed': FriendFeed, 'feed': Feed, 'gmail': GoogleMail, 'greader': GoogleReader}


######
# Main

def main():

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

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    p('\x08\x08Bye!\n')
