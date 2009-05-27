#!/usr/bin/python
# -*- coding: utf-8 -*-
# GPLv3

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, tzinfo
from optparse import OptionParser
from os import path
from StringIO import StringIO
import __builtin__
import elementtree.ElementTree as ET
import imp
import new
import os
import re
import select
import shelve
import signal
import sys
import termios
import threading
import time
import traceback
import tty
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

  for k, v in ANSI.__dict__.iteritems():
    if not k.startswith('_'):
      msg = msg.replace(v, '')
  
  sys.stdout.write('\b \b' * len(msg))
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
    except select.error:
      pass
    except Exception:
      p_err('\n')
      traceback.print_exc()
  return deco


def ftime(d, fmt):

  if d:
    return time.strftime(fmt, d.timetuple())
  else:
    return '!NODATE!'


lurls = {}
lurls['count'] = 0
# TODO limit the numbers
def surl(url):

  global options

  def fmt_url(id):

    if options.local_port == 80:
      new_url = 'http://%s/%d' % (options.local_server, id)
    else:
      new_url = 'http://%s:%d/%d' % (options.local_server, options.local_port, id)
    return new_url

  if not options.local_shortening:
    return url

  # Alredy shortened?
  for id, val in lurls.iteritems():
    if val == url:
      return fmt_url(id)

  new_url = fmt_url(lurls['count'])

  if len(new_url) >= len(url):
    return url

  # Shorter, store it
  lurls[lurls['count']] = url
  lurls['count'] += 1
  return new_url


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


common_tpl_opts = {'ansi': ANSI, 'ftime': ftime, 'surl': surl, 'lurls': lurls}

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

####################################
# xml2dict (modified by me)
# http://code.google.com/p/xml2dict/

class XML2Dict(object):

  @classmethod
  def _parse_node(cls, node):
    node_tree = object_dict()
    # Save attrs and text, hope there will not be a child with same name
    if node.text:
      node_tree.value = node.text
    for (k,v) in node.attrib.items():
      k,v = cls._namespace_split(k, object_dict({'value':v}))
      node_tree[k] = v
    #Save childrens
    for child in node.getchildren():
      tag, tree = cls._namespace_split(child.tag, cls._parse_node(child))
      if  tag not in node_tree: # the first time, so store it in dict
        node_tree[tag] = tree
        continue
      old = node_tree[tag]
      if not isinstance(old, list):
        node_tree.pop(tag)
        node_tree[tag] = [old] # multi times, so change old dict to a list       
      node_tree[tag].append(tree) # add the new one      

    return  node_tree

  @classmethod
  def _namespace_split(cls, tag, value):
    """
    Split the tag  '{http://cs.sfsu.edu/csc867/myscheduler}patients'
       ns = http://cs.sfsu.edu/csc867/myscheduler
       name = patients
    """
    result = re.compile("\{(.*)\}(.*)").search(tag)
    if result:
      value.namespace, tag = result.groups()    
    return (tag, value)

  @classmethod
  def parse(cls, file):
    """parse a xml file to a dict"""
    f = open(file, 'r')
    return cls.fromstring(f.read()) 

  @classmethod
  def fromstring(cls, s):
    """parse a string"""
    t = ET.fromstring(s)
    root_tag, root_tree = cls._namespace_split(t.tag, cls._parse_node(t))
    return object_dict({root_tag: root_tree})


class object_dict(dict):
  """object view of dict, you can 
  >>> a = object_dict()
  >>> a.fish = 'fish'
  >>> a['fish']
  'fish'
  >>> a['water'] = 'water'
  >>> a.water
  'water'
  >>> a.test = {'value': 1}
  >>> a.test2 = object_dict({'name': 'test2', 'value': 2})
  >>> a.test, a.test2.name, a.test2.value
  (1, 'test2', 2)
  """
  def __init__(self, initd=None):
    if initd is None:
      initd = {}
    dict.__init__(self, initd)

  def __getattr__(self, item):
    d = self.__getitem__(item)
    # if value is the only key in object, you can omit it
    if isinstance(d, dict) and 'value' in d and len(d) == 1:
      return d['value']
    else:
      return d

  def __setattr__(self, item, value):
    self.__setitem__(item, value)

####################
# non-blocking stdin

def getch():
  
  global p_stdin

  if p_stdin.poll(1000):
    return sys.stdin.read(1)
  else:
    return None

def ttywidth():

  f = os.popen('tput cols', 'r')
  width = int(f.read())
  f.close()
  return width


def update_width(signum, frame):
  
  global width
  
  width = ttywidth()


def sigexit(signum, frame):

  if 'session' in __builtin__.__dict__:
    session.close()
  termios.tcsetattr(fd, termios.TCSANOW, old_settings)
  p('\033[?25h')


class STDOUT_R:

  @staticmethod
  def write(s):

    s = s.replace('\n', '\r\n')
    sys.__stdout__.write(s.encode('utf-8'))

  @staticmethod
  def flush():

    return sys.__stdout__.flush()


class STDERR_R:

  @staticmethod
  def write(s, *args, **kwds):

    s = s.replace('\n', '\r\n')
    sys.__stderr__.write(s.encode('utf-8'))

  @staticmethod
  def flush():

    return sys.__stderr__.flush()

#########
# Session

def open_session(loc):

  s_path = path.expanduser('~/.clis/session')
  if not path.exists(s_path):
    os.makedirs(s_path, 0700)
  filename = '%s/%s' % (s_path, hash(loc))
  __builtin__.session = shelve.open(filename, writeback=True)
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
    p_clr(msg)

  session.__dict__['do_sync'] = new.instancemethod(do_sync, session, dict)
  p_dbg('Session file %s opened' % filename)

##############
# Source class

class Source(object):

  TYPE = 'unknown'
  TPL_ACCESS = tpl('@!ansi.fired!@Accessing [@!src_name!@] @!src_id!@...@!ansi.freset!@', escape=None)
  CHECK_LIST_SIZE = 20

  def _init_session(self):
    
    session_id = '%s:%s' % (self.TYPE, self.src_id)
    if session_id not in session:
      # New source, need to initialize
      p_dbg('New source: [%s]' % session_id)
      session[session_id] = {}
    self.session = session[session_id]
    self.session_id = session_id

  # The following two functions simplely use last entry's id to check, usually
  # helpful source can query with parameter like since_id or starting date.
  def _load_last_id(self):

    if 'last_id' in self.session:
      self.last_id = self.session['last_id']
      p_dbg('Session [%s] last_id = "%s"' % (self.session_id, self.last_id))
    else:
      self._update_last_id(None)

  def _update_last_id(self, last_id):

    self.last_id = last_id
    self.session['last_id'] = last_id
    session[self.session_id] = self.session
    p_dbg('Updating [%s] last_id to %s' % (self.session_id, session[self.session_id]['last_id']))

  # The following three functions store a list of entries' id and updated, then
  # use the list to compare. The length of the list should be larger than the
  # amount of entries in feed. Default is 20.
  def is_new_item(self, entry):
    '''Check if entry is new and also update check_list if it is new'''
    e_id = self.get_entry_id(entry)
    e_updated = self.get_entry_updated(entry)
    if e_id in self.check_list:
      if e_updated <= self.check_list[e_id]:
        return False
    self.check_list[e_id] = e_updated
    return True

  def _load_check_list(self):

    if 'check_list' in self.session:
      self.check_list = self.session['check_list']
      p_dbg('Session [%s] checklist loaded' % self.session_id)
    else:
      self.check_list = {}
      p_dbg('Session [%s] checklist initialized' % self.session_id)

  def _update_check_list(self):
    '''Limit items in check_list'''
    
    lst = self.check_list.items()
    lst.sort(key=lambda x: x[1], reverse=True)
    # Limit the size
    lst = lst[:self.CHECK_LIST_SIZE]
    self.check_list = dict(lst)
    self.session['check_list'] = self.check_list
    session[self.session_id] = self.session
    p_dbg('Updated [%s] check_list' % self.session_id)

  @staticmethod
  def get_entry_id(entry):

    if 'guid' in entry:
      return entry['guid']
    if 'id' in entry:
      return entry['id']
    return entry['title'] + entry['link']

  @staticmethod
  def get_entry_updated(entry):
    '''Decide the last updated of the entry
    The date object must be a datetime. If none date is found, then it assign
    the current local time to key updated.'''
    dates = []
    for key in ['updated', 'published', 'created']:
      if key in entry:
        dates += [entry[key]]
    if not dates:
      entry['updated'] = datetime.now()
      return entry['updated']
    return max(dates)

  def datetimeize(self, entry):
    '''Convert all date to datetime in localtime'''
    for key in ['updated', 'published', 'created', 'expired']:
      if key in entry:
        entry[key] = self.to_localtime(entry[key])

  @staticmethod
  def to_localtime(d):
    '''Convert UTC datetime to localtime datetime'''
    return datetime(*d[:6]).replace(tzinfo=utc).astimezone(local_tz)

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    feed = self.get_list()
    p_clr(msg)
    if not feed['entries']:
      return
      
    entries = []
    if self.CHECK_LIST_SIZE < len(feed['entries'] * 2):
      self.CHECK_LIST_SIZE = len(feed['entries'] * 2)
      p_dbg('Changed CHECK_LIST_SIZE to %d' % self.CHECK_LIST_SIZE)
    # Get entries after last_id
    for entry in feed['entries']:
      self.datetimeize(entry)
      if not self.is_new_item(entry):
         continue
      entries += [entry]
    # Update last_id
    if entries:
      self._update_check_list()

    entries.reverse()
    for entry in entries:
      p_dbg('ID: %s' % self.get_entry_id(entry))
      print self.output(entry=entry, src_name=self.src_name, **common_tpl_opts)


class Twitter(Source):

  TYPE = 'twitter'

  def __init__(self, src):
    
    self.last_accessed = 0
    self.username = src['username']
    self.api = twitter.Api(username=self.username, password=src['password'])
    self.src_id = self.username
    self.src_name = src.get('src_name', 'Twitter')
    self.interval = src.get('interval', 90)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(status.created_at, "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!status.user.screen_name!@@!ansi.freset!@: @!status.text!@ @!ansi.fmagenta!@@!surl(status.tweet_link)!@@!ansi.freset!@'), escape=None)

    self._init_session()
    self._load_last_id()

  @staticmethod
  def to_localtime(d):

    return datetime(*fp._parse_date(d)[:6]).replace(tzinfo=utc).astimezone(local_tz)

  def get_list(self):

    return self.api.GetFriendsTimeline(since_id=self.last_id)

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    try:
      p(msg)
      statuses = self.get_list()
      p_clr(msg)
    except urllib2.HTTPError, e:
      # TODO for 503 should follow this:
      # http://apiwiki.twitter.com/Rate-limiting
      if e.code != 200:
        p_err('CODE %d' % e.code)
        return

    if not statuses:
      return
    self._update_last_id(statuses[0].id)

    statuses.reverse()
    for status in statuses:
      p_dbg('ID: %s' % status.id)
      status.__dict__['tweet_link'] = 'http://twitter.com/%s/status/%s' % (status.user.screen_name, status.id)
      status.created_at = self.to_localtime(status.created_at)
      print self.output(status=status, src_name=self.src_name, **common_tpl_opts)


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
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["user"]["nickname"]!@@!ansi.freset!@:<!--(if "room" in entry)--> @!ansi.fiyellow!@[@!entry["room"]["name"]!@]@!ansi.freset!@<!--(end)--> @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@@!surl(entry["_link"])!@@!ansi.freset!@'), escape=None)
    self.output_like = tpl(src.get('output_like', '@!ansi.fgreen!@@!ftime(like["date"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!like["user"]["nickname"]!@@!ansi.freset!@ @!ansi.fired!@♥@!ansi.freset!@ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@@!surl(entry["_link"])!@@!ansi.freset!@'), escape=None)
    self.output_comment = tpl(src.get('output_comment', '@!ansi.fgreen!@@!ftime(comment["date"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!comment["user"]["nickname"]!@@!ansi.freset!@ ✎ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@: @!comment["body"]!@ @!ansi.fmagenta!@@!surl(entry["_link"])!@@!ansi.freset!@'), escape=None)
    self.show_like = src.get('show_like', True)
    self.show_comment = src.get('show_comment', True)
    self.show_hidden = src.get('show_hidden', False)

  @staticmethod
  def to_localtime(d):
    
    return d.replace(tzinfo=utc).astimezone(local_tz)

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
      if entry['hidden'] and not self.show_hidden:
        continue
      entry['_link'] = 'http://friendfeed.com/e/' + entry["id"]
      if entry['is_new']:
        entry['updated'] = self.to_localtime(entry['updated'])
        print self.output(entry=entry, src_name=self.src_name, **common_tpl_opts)

      if self.show_like:
        for like in entry['likes']:
          if like['is_new']:
            like['date'] = self.to_localtime(like['date'])
            print self.output_like(like=like, entry=entry, src_name=self.src_name, **common_tpl_opts)

      if self.show_comment:
        for comment in entry['comments']:
          if comment['is_new']:
            comment['date'] = self.to_localtime(comment['date'])
            print self.output_comment(comment=comment, entry=entry, src_name=self.src_name, **common_tpl_opts)


class Feed(Source):

  TYPE = 'feed'

  def __init__(self, src):
    
    self.last_accessed = 0
    self.feed = src['feed']
    # Used as key to store session data
    self.src_id = self.feed
    self.src_name = src.get('src_name', 'Feed')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry.link)!@@!ansi.fmagenta!@@!ansi.freset!@@!ansi.freset!@'), escape=None)

    self._init_session()
    self._load_check_list()

  def datetimeize(self, entry):
    '''Replace date with parsed date then do Source.datetimeize'''
    for key in ['updated', 'published', 'created', 'expired']:
      if key + '_parsed' in entry:
        entry[key] = entry[key + '_parsed']
        del entry[key + '_parsed']
    Source.datetimeize(self, entry)

  def get_list(self):

    return fp.parse(self.feed)


class TwitterSearch(Feed):

  TYPE = 'twittersearch'
  SEARCH_URL = 'http://search.twitter.com/search.atom'
  RE_LINK = re.compile('(.*?)<a href="(.*?)">(.*?)</a>(.*)', re.DOTALL)

  def __init__(self, src):
    
    self.last_accessed = 0
    self.src_name = src.get('src_name', 'TwitterSearch')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["published"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["author"]["screen_name"]!@@!ansi.freset!@: @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry["link"])!@@!ansi.freset!@'), escape=None)
    self.q = src['q']
    self.lang = src.get('lang', 'en')
    self.src_id = '%s:%s' % (self.lang, self.q)
    self.rpp = src.get('rpp', 15)
    self.hl_words = self.q.split(' ')

    self._init_session()
    self._load_last_id()

  # Copied from my old code, twitter-tracker. 
  def cleanup_links(self, s):

    m = self.RE_LINK.match(s)
    while m:
      if m.group(2) == str(m.group(3)).replace('<b>', '').replace('</b>', '') or \
          m.group(2).find(m.group(3)) >= 0:
        # Other links metioned in tweets
        s = "%s\033[1:33m%s\033[0m%s" % (m.group(1), surl(m.group(2)), m.group(4))
      else:
        if m.group(2)[0] == '/':
          # A hashtag has uri /search?q=%23... 
          s = "%s\033[1:32m%s\033[0m%s" % (m.group(1), surl(m.group(3)), m.group(4))
        else:
          # User
          s = "%s%s[\033[1:34m%s\033[0m]%s" % (m.group(1), m.group(3), surl(m.group(2)), m.group(4))
      m = self.RE_LINK.match(s)
    return s
  
  def unescape(self, s):
    
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&")
    return s

  def get_list(self):

    parameters = {'q': self.q, 'lang': self.lang, 'rpp': self.rpp}
    if self.last_id:
      parameters['since_id'] = self.last_id
    feed = fp.parse(self.SEARCH_URL + '?' + urllib.urlencode(parameters))

    # FIXME
    try:
      for link in feed.feed.links:
        if link.rel == 'refresh':
          self._update_last_id(link.href.rsplit('=', 1)[1])
          break
    except AttributeError, e:
      print feed.feed
      traceback.print_exc()
      raise e

    for entry in feed['entries']:
      entry['title'] = self.cleanup_links(self.unescape(entry['content'][0]['value'])).replace('<b>', ANSI.fred).replace('</b>', ANSI.freset).replace('\n', ' ')
      screen_name, name = entry['author'].split(' ', 1)
      entry['author'] = {'screen_name': screen_name, 'name': name[1:-1]}

    return feed

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    feed = self.get_list()
    p_clr(msg)
    if not feed['entries']:
      return
      
    entries = feed['entries']
    # Get entries after last_id
    for entry in entries:
      self.datetimeize(entry)

    entries.reverse()
    for entry in entries:
      p_dbg('ID: %s' % self.get_entry_id(entry))
      print self.output(entry=entry, src_name=self.src_name, **common_tpl_opts)


# http://stackoverflow.com/questions/52880/google-reader-api-unread-count
class GoogleBase(Feed):

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


class GoogleMail(Feed):

  TYPE = 'gmail'

  def __init__(self, src):
    
    self.last_accessed = 0
    self.email = src['email']
    self.password = src['password']
    self.src_id = self.email
    self.src_name = src.get('src_name', 'Gmail')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ @!ansi.fred!@[@!src_name!@]@!ansi.freset!@ @!ansi.fyellow!@@!entry["author"]!@@!ansi.freset!@: @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry["link"])!@@!ansi.freset!@'), escape=None)

    self._init_session()
    self._load_check_list()

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
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["source"]["title"]!@@!ansi.freset!@: @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry["link"])!@@!ansi.freset!@'), escape=None)
    
    self._init_session()
    self._load_check_list()

  def get_list(self):

    content = self.get('http://www.google.com/reader/atom/user%2F-%2Fstate%2Fcom.google%2Freading-list')
    return fp.parse(content)


class Weather(Source):

  TYPE = 'weather'
  COUNT = 0
  PARTNER_ID = '1118660757'
  LICENSE_KEY = '26ae171b4be6178b'
  XOAP_URI = 'http://xoap.weather.com/weather/local/%%s?cc=*&unit=%%s&link=xoap&prod=xoap&par=%s&key=%s' % (PARTNER_ID, LICENSE_KEY)

  def __init__(self, src):

    if self.COUNT >= 3:
      # display weather data for no more than three (3) locations at a time;
      # Because of "at a time", I think the term doesn't really can restrict
      # clis, but I just limit for that.
      p_err('You can only use upto three Weather sources')
      return None

    self.last_accessed = 0
    self.locid = src['locid']
    self.unit = src.get('unit', 'm')
    self.src_id = self.locid
    self.src_name = src.get('src_name', 'Weather')
    # in minutes
    # TODO add forcast interval
    self.interval = src.get('interval', 30) * 60
    if self.interval < 25:
      p_err('Weather update interval must longer than or equal to 25 minutes, forced to 30 minutes')
      self.interval = 30
    # provide four (4) promotional links, selected by TWCi and provided through
    # the Service on each data call, back to www.weather.com for additional
    # weather information in close proximity to the TWCi Content as set forth
    # in Exhibit B of the Agreement;
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(weather["cc"]["lsup"], "%H:%M:%S")!@@!ansi.freset!@ @!ansi.fred!@[@!src_name!@]@!ansi.freset!@ @!ansi.fyellow!@@!weather["cc"]["obst"]!@@!ansi.freset!@ Temperature: @!weather["cc"]["tmp"]!@°@!weather["head"]["ut"]!@ Feels like: @!weather["cc"]["flik"]!@°@!weather["head"]["ut"]!@ Conditions: @!weather["cc"]["t"]!@ Wind: <!--(if weather["cc"]["wind"]["s"] == "calm")-->calm<!--(else)-->@!weather["cc"]["wind"]["s"]!@@!weather["head"]["us"]!@ (@!int(float(weather["cc"]["wind"]["s"]) * 0.6214)!@mph) (@!weather["cc"]["wind"]["t"]!@)<!--(end)--> (Provided by weather.com; @!weather["lnks"]["link"][0]["t"]!@: @!surl(weather["lnks"]["link"][0]["l"])!@ @!weather["lnks"]["link"][1]["t"]!@: @!surl(weather["lnks"]["link"][1]["l"])!@ @!weather["lnks"]["link"][2]["t"]!@: @!surl(weather["lnks"]["link"][2]["l"])!@ @!weather["lnks"]["link"][3]["t"]!@: @!surl(weather["lnks"]["link"][3]["l"])!@)'), escape=None)
    self.COUNT += 1

  @staticmethod
  def to_localtime(d):

    return datetime.strptime(d, '%m/%d/%y %I:%M %p Local Time')

  def get(self):

    f = urllib2.urlopen(self.XOAP_URI % (self.locid, self.unit))
    d = XML2Dict.fromstring(f.read())['weather']
    f.close()
    # make {"a" : {"value": "abc"} be {"a": "value"}
    def _simplify(d):
      for k, v in d.iteritems():
        if isinstance(d[k], dict):
          if len(v) == 1 and 'value' in v:
            d[k] = v['value']
          else:
            _simplify(d[k])
        elif isinstance(d[k], list):
          for item in d[k]:
            _simplify(item)
    _simplify(d)

    return d

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    weather = self.get()
    p_clr(msg)
    
    weather['cc']['lsup'] = self.to_localtime(weather['cc']['lsup'])
    try:
      print self.output(weather=weather, src_name=self.src_name, **common_tpl_opts)
    except:
      from pprint import pprint
      pprint(weather)
      traceback.print_exc()


class PunBB12(Feed):

  TYPE = 'punbb12'
  RE_PUBLISHED = re.compile(r'Posted: (.*?)<br />')
  RE_UPDATED = re.compile(r'Last post: (.*?)$')

  def get_list(self):

    feed = fp.parse(self.feed)
    for entry in feed['entries']:
      # TODO parse category
      entry['published_parsed'] = fp._parse_date(self.RE_PUBLISHED.search(entry['description']).groups()[0])
      entry['updated_parsed'] = fp._parse_date(self.RE_UPDATED.search(entry['description']).groups()[0])
    return feed

SOURCE_CLASSES = {'twitter': Twitter, 'friendfeed': FriendFeed, 'feed': Feed,
    'gmail': GoogleMail, 'greader': GoogleReader, 'weather': Weather,
    'punbb12': PunBB12, 'twittersearch': TwitterSearch}

##################
# Local shortening

# Not really do shorten in the server, it is only do redirection
class ShorteningHandler(BaseHTTPRequestHandler):

  def do_GET(self):

    p_dbg('HTTP Req: %s' % self.path)
    try:
      id = int(self.path[1:])
      if id not in lurls:
        raise ValueError
    except ValueError:
      self.send_error(400, 'Invalid code')
      return
    p_dbg('HTTP Redirecting to %s' % lurls[id])
    self.send_response(307)
    self.send_header('Content-Type', 'text/html')
    self.send_header('Location', lurls[id])
    self.end_headers()

  def log_message(self, *args):

    pass


class HTTPThread(threading.Thread):

  def run(self):

    httpd = HTTPServer((options.local_server, int(options.local_port)), ShorteningHandler)
    p_dbg('Local shortening server started')
    httpd.serve_forever()

################
# Option Handler

def parser_args():

  parser = OptionParser()

  parser.add_option('-c', '--config', dest='config_file',
      default='', help='Specify a configuration to use')
  parser.add_option('-d', '--debug', dest='debug', action='store_true',
      default=False, help='Show debug messages')
  parser.add_option('-l', '--no-local-shortening', dest='local_shortening', action='store_false',
      default=True, help='Disable local shortening')
  parser.add_option('-s', '--local-server', dest='local_server',
      default=None, help='Address of local shortening server (Default: localhost)')
  parser.add_option('-p', '--local-port', dest='local_port',
      default=None, help='Which port to listen (Default: 8080)')

  options, args = parser.parse_args()

  if options.local_port:
    options.local_port = int(options.local_port)
  __builtin__.DEBUG = options.debug

  return options, args

######
# Main

def main():

  global options

  p('''clis (C) 2009 Yu-Jie Lin
The code is licensed under the terms of the GNU General Public License (GPL).

For running the code, you must agree with all limitations which are denoted in
clis_cfg-sample.py, read the file for more information.\n\n''')

  # Process arguments
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
    sigexit(None, None)
    sys.exit(1)
  # Configure server parameter
  # FIXME this is ugly
  if hasattr(cfg, 'server'):
    if options.local_server is None:
      options.local_server = cfg.server['name']
    if options.local_port is None:
      options.local_port = cfg.server['port']
  if options.local_server is None:
    options.local_server = 'localhost' 
  if options.local_port is None:
    options.local_port = 8080
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
  # cfg is no need to stay
  del cfg
  
  if options.local_shortening:
    http_thread = HTTPThread()
    # Make it exit with main
    http_thread.setDaemon(True)
    http_thread.start()
  # Give some time for server, better looking output
  time.sleep(0.1)
  p('Initialized.\n')

  while True:
    try:
      for src in sources:
        src.update()
      session.do_sync(sources)
      ch = getch()
      if ch:
        if ch == 'q':
          break
        if ch == "\x03":
          # Ctrl+C
          break
        if ch == "\x0d":
          # Entry key
          p('\033[97;101m' + '-' * width + '\n\033[39;49m')
    except select.error:
      # Conflict with signal
      # select.error: (4, 'Interrupted system call') on p.poll(1)
      pass


if __name__ == '__main__':
  
  p('\033[?25l')
  width = ttywidth()
  signal.signal(signal.SIGWINCH, update_width)

  # Get stdin file descriptor
  fd = sys.stdin.fileno()         
  # Backup, important!
  old_settings = termios.tcgetattr(fd)
  tty.setraw(sys.stdin.fileno())

  p_stdin = select.poll()
  # Register for data-in
  p_stdin.register(sys.stdin, select.POLLIN)

  sys.stdout = STDOUT_R
  sys.stderr = STDERR_R

  try:
    main()
  except Exception, e:
    sigexit(None, None)
    traceback.print_exc()
    raise e
  p('Bye!\n')
  sigexit(None, None)
