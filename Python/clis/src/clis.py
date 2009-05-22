#!/usr/bin/python
# -*- coding: utf-8 -*-
# GPLv3
# References
# http://code.google.com/p/python-twitter/
# http://code.google.com/p/friendfeed-api/
# http://feedparser.org/
# Todo
# TODO Store session data
# TODO flatten dict or a better templating

from datetime import datetime, timedelta, tzinfo
from optparse import OptionParser
from os import path
import __builtin__
import imp
import new
import os
import shelve
import sys
import time
import traceback
import urllib
import urllib2

from pyratemp import Template as tpl

import feedparser as fp
import friendfeed as ff
import twitter

###########
# Utilities

TPL_P_ERR = tpl('@!ansi.fiwhite!@@!ansi.bired!@ERROR: @!error!@@!ansi.breset!@@!ansi.freset!@', escape=None)
TPL_P_DBG = tpl('@!ansi.fiwhite!@@!ansi.biblue!@DEBUG: @!msg!@@!ansi.breset!@@!ansi.freset!@', escape=None)


def p(msg):

  sys.stdout.write(msg)
  sys.stdout.flush()


def p_clr(msg):

  sys.stdout.write('\x0d' + ' ' * len(msg) + '\x0d')
  sys.stdout.flush()


def p_err(error):
  
  p(TPL_P_ERR(ansi=ANSI, error=error))


def p_dbg(msg, newline=True):

  if DEBUG:
    p(TPL_P_DBG(ansi=ANSI, msg=msg))
    if newline:
      p('\n')


def safe_update(func):
  
  def deco(*args, **kwds):
    try:
      func(*args, **kwds)
    except Exception:
      p_err('\n')
      traceback.print_exc()
  return deco

##################
# ANSI escape code

class ANSI:

  # http://en.wikipedia.org/wiki/ANSI_escape_code
  reset = '\033[0m'
  bold = '\033[1m'
  underline = '\033[4m'
  blink = '\033[5m'
  no_underline = '\033[24m'
  no_blink = '\033[25m'
  fblack = '\033[30m'
  fred = '\033[31m'
  fgreen = '\033[32m'
  fyellow = '\033[33m'
  fblue = '\033[34m'
  fmagenta = '\033[35m'
  fcyan = '\033[36m'
  fwhite = '\033[37m'
  freset = '\033[39m'
  bblack = '\033[40m'
  bred = '\033[41m'
  bgreen = '\033[42m'
  byellow = '\033[43m'
  bblue = '\033[44m'
  bmagenta = '\033[45m'
  bcyan = '\033[46m'
  bwhite = '\033[47m'
  breset = '\033[49m'
  fiblack = '\033[90m'
  fired = '\033[91m'
  figreen = '\033[92m'
  fiyellow = '\033[93m'
  fiblue = '\033[94m'
  fimagenta = '\033[95m'
  ficyan = '\033[96m'
  fiwhite = '\033[97m'
  biblack = '\033[100m'
  bired = '\033[101m'
  bigreen = '\033[102m'
  biyellow = '\033[103m'
  biblue = '\033[104m'
  bimagenta = '\033[105m'
  bicyan = '\033[106m'
  biwhite = '\033[107m'
  # Default background color
#  b = bblack

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

#########
# Session

def open_session(loc):

  s_path = path.expanduser('~/.clis/session')
  if not path.exists(s_path):
    os.makedirs(s_path, 0700)
  filename = '%s/%s' % (s_path, hash(loc))
  __builtin__.session = shelve.open(filename)#, writeback=True)
  session['config'] = loc
  session.__dict__['last_sync'] = time.time()
  session.__dict__['interval'] = 60

  def do_sync(self, sources):

    if time.time() < self.interval + self.last_sync:
      return
    self.last_sync = time.time()
  
    msg = 'Saving session data...'
    p(msg)
    self.sync()
#    for src in sources:
#      self[src.session_id] = src.session
    p_clr(msg)

  session.__dict__['do_sync'] = new.instancemethod(do_sync, session, dict)
  p_dbg('Session file %s opened' % filename)

##############
# Source class

class Source(object):

  TYPE = 'unknown'
  TPL_ACCESS = tpl('@!ansi.fired!@Accessing [@!src_name!@] @!src_id!@...@!ansi.freset!@', escape=None)

  def _init_session(self):
    
    session_id = '%s:%s' % (self.TYPE, self.src_id)
    if session_id not in session:
      # New source, need to initialize
      p_dbg('New source: [%s]' % session_id)
      session[session_id] = {}
    self.session = session[session_id]
    self.session_id = session_id

  def _load_last_id(self):

    if 'last_id' in self.session:
      self.last_id = self.session['last_id']
      p_dbg('Session [%s] last_id = "%s"' % (self.session_id, self.last_id))
    else:
      self._update_last_id(None)

  def _update_last_id(self, last_id):

    p_dbg('Updating [%s] last_id to %s' % (self.session_id, last_id))
    self.last_id = last_id
    self.session['last_id'] = last_id
    session[self.session_id] = self.session

  @staticmethod
  def get_entry_id(entry):

    # TODO hash?
    if 'id' in entry:
      return entry['id']
    # TODO More?
    return entry['title'] + entry['link']

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    feed = self.get_list()
    p_clr(msg)
    entries = []
    if feed['entries']:
      # Get entries after last_id
      for entry in feed['entries']:
        if self.last_id == self.get_entry_id(entry):
           break
        entries += [entry]
    # Update last_id
    if entries:
      self._update_last_id(self.get_entry_id(entries[0]))

    entries.reverse()
    for entry in entries:
      p_dbg('ID: %s' % self.get_entry_id(entry))
      try:
        entry['updated'] = datetime(*entry['updated_parsed'][:6]).replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
      except KeyError:
        entry['updated'] = 'NOUPDATE'
      print self.output(entry=entry, ansi=ANSI, src_name=self.src_name)


class Twitter(Source):

  TYPE = 'twitter'

  def __init__(self, src):
    
    self.last_accessed = 0
    self.username = src['username']
    self.api = twitter.Api(username=self.username, password=src['password'])
    self.src_id = self.username
    self.src_name = src.get('src_name', 'Twitter')
    self.interval = src.get('interval', 90)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!status.created_at!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!status.user.screen_name!@@!ansi.freset!@: @!status.text!@ @!ansi.fmagenta!@http://twitter.com/@!status.user.screen_name!@/status/@!status.id!@@!ansi.freset!@'), escape=None)
    self.date_fmt = src.get('date_fmt', '%H:%M:%S')

    self._init_session()
    self._load_last_id()

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    try:
      p(msg)
      if self.last_id:
        statuses = self.api.GetFriendsTimeline(since_id=self.last_id)
      else:
        statuses = self.api.GetFriendsTimeline()
      p_clr(msg)
    except urllib2.HTTPError, e:
      # TODO for 503 should follow this:
      # http://apiwiki.twitter.com/Rate-limiting
      if e.code != 200:
        p_err(' CODE %d' % e.code)
        return

    if statuses:
      self._update_last_id(statuses[0].id)

    statuses.reverse()
    for status in statuses:
      # FIXME
      status.created_at = datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
#      status.link = 'http://twitter.com/%s/status/%d' % (status.user.screen_name, status.id)
      print self.output(status=status, ansi=ANSI, src_name=self.src_name)


class FriendFeed(Source):

  TYPE = 'friendfeed'

  def __init__(self, src):

    self.last_accessed = 0
    self.token = None
    self.nickname = src['nickname']
    self.api = ff.FriendFeed(self.nickname, src['remote_key'])
    self.src_id = self.nickname
    self.src_name = src.get('src_name', 'FriendFeed')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["user"]["nickname"]!@@!ansi.freset!@:<!--(if "room" in entry)--> @!ansi.fiyellow!@[@!entry["room"]["name"]!@]@!ansi.freset!@<!--(end)--> @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@http://friendfeed.com/e/@!entry["id"]!@@!ansi.freset!@'), escape=None)
    self.output_like = tpl(src.get('output_like', '@!ansi.fgreen!@@!like["date"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!like["user"]["nickname"]!@@!ansi.freset!@ @!ansi.fired!@♥@!ansi.freset!@ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@http://friendfeed.com/e/@!entry["id"]!@@!ansi.freset!@'), escape=None)
    self.output_comment = tpl(src.get('output_comment', '@!ansi.fgreen!@@!comment["date"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!comment["user"]["nickname"]!@@!ansi.freset!@ ✎ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@: @!comment["body"]!@ @!ansi.fmagenta!@http://friendfeed.com/e/@!entry["id"]!@@!ansi.freset!@'), escape=None)
    self.show_like = src.get('show_like', True)
    self.show_comment = src.get('show_comment', True)
    self.date_fmt = src.get('date_fmt', '%H:%M:%S')

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    if not self.token:
      self.token = self.api.fetch_updates()['update']['token']

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    home = self.api.fetch_updates_home(token=self.token, timeout=0)
    p_clr(msg)
    self.token = home['update']['token']

    entries = home['entries']
    for entry in entries:
      if entry['is_new']:
        # FIXME
        entry['updated'] = entry['updated'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
        print self.output(entry=entry, ansi=ANSI, src_name=self.src_name)

      if self.show_like:
        for like in entry['likes']:
          if like['is_new']:
            # FIXME
            like['date'] = like['date'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
            print self.output_like(like=like, entry=entry, ansi=ANSI, src_name=self.src_name)

      if self.show_comment:
        for comment in entry['comments']:
          if comment['is_new']:
            # FIXME
            comment['date'] = comment['date'].replace(tzinfo=utc).astimezone(local_tz).strftime(self.date_fmt)
            print self.output_comment(comment=comment, entry=entry, ansi=ANSI, src_name=self.src_name)


class Feed(Source):

  TYPE = 'feed'

  def __init__(self, src):
    
    self.last_accessed = 0
    self.feed = src['feed']
    # Used as key to store session data
    self.src_id = self.feed
    self.src_name = src.get('src_name', 'Feed')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!entry.link!@@!ansi.freset!@'), escape=None)
    self.date_fmt = src.get('date_fmt', '%H:%M:%S')

    self._init_session()
    self._load_last_id()

  def get_list(self):

    return fp.parse(self.feed)


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

  TYPE = 'gmail'

  def __init__(self, src):
    
    self.last_accessed = 0
    self.email = src['email']
    self.password = src['password']
    self.src_id = self.email
    self.src_name = src.get('src_name', 'Gmail')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ @!ansi.fred!@[@!src_name!@]@!ansi.freset!@ @!ansi.fyellow!@@!entry["author"]!@@!ansi.freset!@: @!ansi.bold!@@!entry["title"]!@@!ansi.reset!@ @!entry["link"]!@'), escape=None)
    self.date_fmt = src.get('date_fmt', '%H:%M:%S')

    self._init_session()
    self._load_last_id()

  def get_list(self):

    # FIXME Check if we can use ClientLogin, don't like password being stored
    feed = fp.parse('https://%s:%s@mail.google.com/mail/feed/atom' % (urllib.quote(self.email), urllib.quote(self.password)))
    return feed


class GoogleReader(GoogleBase):

  TYPE = 'greader'

  def __init__(self, src):
    
    GoogleBase.__init__(self, src)

    self.last_accessed = 0
    self.src_id = self.email
    self.src_name = src.get('src_name', 'GR')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["source"]["title"]!@@!ansi.freset!@@!ansi.freset!@: @!ansi.bold!@@!entry["title"]!@@!ansi.reset!@ @!entry["link"]!@'), escape=None)
    self.date_fmt = src.get('date_fmt', '%H:%M:%S')
    
    self._init_session()
    self._load_last_id()

  def get_list(self):

    content = self.get('http://www.google.com/reader/atom/user%2F-%2Fstate%2Fcom.google%2Freading-list')
    return fp.parse(content)


SOURCE_CLASSES = {'twitter': Twitter, 'friendfeed': FriendFeed, 'feed': Feed, 'gmail': GoogleMail, 'greader': GoogleReader}


################
# Option Handler

def parser_args():

  parser = OptionParser()

  parser.add_option('-c', '--config', dest='config_file',
      default='', help='Specify a configuration to use')
  parser.add_option('-d', '--debug', dest='debug', action='store_true',
      default=False, help='Show debug messages (default: %default)')

  options, args = parser.parse_args()

  __builtin__.DEBUG = options.debug

  return options, args

######
# Main

def main():

  # Provess arguments
  options, args = parser_args()

  # Load configuration
  cfg_loc = filter(path.exists, [path.abspath('clis_cfg.py'), path.abspath('clis_cfg'),
      path.expanduser('~/.clis_cfg.py'), path.expanduser('~/.clis_cfg')])
  if options.config_file:
    cfg_loc = [options.config_file] + cfg_loc
  cfg = None
  for loc in cfg_loc:
    f = None
    try:
      f = open(loc, 'U')
      cfg = imp.load_module('cfg', f, loc, ('.py', 'U', imp.PY_SOURCE))
      p('Initializing configuration from %s...\n' % loc)
    except IOError:
      p_err('Unable to open configuration from %s\n' % loc)
    except (ImportError, SyntaxError):
      # TODO print out necessary parts
      p_err('Unable to load configuration from %s\n' % loc)
      traceback.print_exc()
    finally:
      if f:
        f.close()
      if cfg:
        break
  if not cfg:
    p_err('No configuration is available, exit.\n')
    sys.exit(1)
  # Prepare session
  open_session(loc)

  sources = []
  for src in cfg.sources:
    if 'type' not in src:
      p_err('Source type unspecified: %s\n' % repr(src))
      continue
    if src['type'] in SOURCE_CLASSES:
      sources.append(SOURCE_CLASSES[src['type']](src))
    else:
      p_err('Unknown source type: %s' % src['type'])
  p('Initialized.\n')

  try:
    while True:
      for src in sources:
        src.update()
      session.do_sync(sources)
      time.sleep(1)
  except KeyboardInterrupt:
    pass
  session.close()

if __name__ == '__main__':
  main()
  p('\x08\x08Bye!\n')
