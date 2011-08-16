#!/usr/bin/python
# -*- coding: utf-8 -*-
# clis - CLI Stream Reader
# Copyright 2009, 2010, Yu-Jie Lin
# GPLv3

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, tzinfo
from optparse import OptionParser
from os import path
from StringIO import StringIO
import __builtin__
import elementtree.ElementTree as ET
import imp
import json
import new
import os
import re
import select
import shelve
import signal
import socket
import stat
import sys
import termios
import threading
import time
import traceback
import tty
import urllib
import urllib2
import urlparse
socket.setdefaulttimeout(10)

from pyratemp import Template as tpl

import feedparser as fp
import friendfeed as ff
import oauth2 as oauth 


###############
# Twitter OAuth

request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
authorize_url = 'https://api.twitter.com/oauth/authorize'

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
    except (socket.error, socket.timeout, urllib2.HTTPError, urllib2.URLError), e:
      p_err('%s\n' % repr(e))
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


def unescape(s):
  
  s = s.replace("&lt;", "<")
  s = s.replace("&gt;", ">")
  s = s.replace("&quot;", '"')
  s = s.replace("&amp;", "&")
  return s


def remove_additional_space(s):

  return re.sub('( |\n|\t)+', ' ', s)


# A very simple version of tags stripping, it might be buggy
RE_STRIP_TAGS = re.compile(ur'<.*?>', re.IGNORECASE | re.MULTILINE | re.DOTALL | re.UNICODE)

def strip_tags(s):

  while True:
    s1 = RE_STRIP_TAGS.sub('', s)
    if s1 == s:
      break
    s = s1
  return s1


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


common_tpl_opts = {
    'ansi': ANSI,
    'ftime': ftime,
    'surl': surl, 'lurls': lurls,
    'unescape': unescape,
    'remove_additional_space': remove_additional_space,
    'strip_tags': strip_tags,
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
  if fd is not None and old_settings is not None:
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

  def __init__(self, src):

    self.last_accessed = 0
    self.include = src.get('include', [])
    self.exclude = src.get('exclude', [])
    self.highlight = src.get('highlight', [])
    self.hide_id = src.get('hide_id', False)

    self.RE_INCLUDE = {}
    for key, includes in self.include:
      self.RE_INCLUDE[key] = re.compile(u'(' + u'|'.join(includes) + u')', re.I | re.U)
    self.RE_EXCLUDE = {}
    for key, excludes in self.exclude:
      self.RE_EXCLUDE[key] = re.compile(u'(' + u'|'.join(excludes) + u')', re.I | re.U)

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
      if key in entry and entry[key]:
        dates += [entry[key]]
    if not dates:
      entry['updated'] = datetime.utcnow().replace(tzinfo=utc)
      return entry['updated']
    return max(dates)

  def datetimeize(self, entry):
    '''Convert all date to datetime in localtime'''
    for key in ['updated', 'published', 'created', 'expired']:
      if key in entry and entry[key]:
        # XXX
        try:
          entry[key] = self.to_localtime(entry[key])
        except Exception, e:
          print entry
          raise e

  @staticmethod
  def to_localtime(d):
    '''Convert UTC datetime to localtime datetime'''
    return datetime(*d[:6]).replace(tzinfo=utc).astimezone(local_tz)

  def is_included(self, entry):

    for key in self.RE_INCLUDE.keys():
      try:
        # FIXME Dangerous
        value = eval('entry%s' % key)
        if key == '["tags"]':
          # Specially for feed class
          for tag in value:
            if self.RE_INCLUDE[key].search(tag['term']):
              p_dbg('Included %s: Category %s' % (key, tag['term']))
              return True
        elif self.RE_INCLUDE[key].search(value):
          # The value of key is not a list
          p_dbg('Included %s: %s' % (key, value))
          return True
      except Exception, e:
        p_err('[%s][is_included] %s' % (self.session_id, repr(e)))
        raise e
    return False

  def is_excluded(self, entry):

    for key in self.RE_EXCLUDE.keys():
      try:
        # FIXME Dangerous
        value = eval('entry%s' % key)
        if key == '["tags"]':
          # Specially for feed class
          for tag in value:
            if self.RE_EXCLUDE[key].search(tag['term']):
              p_dbg('Excluded %s: Category %s' % (key, tag['term']))
              return True
        elif self.RE_EXCLUDE[key].search(value):
          # The value of key is not a list
          p_dbg('Excluded %s: %s' % (key, value))
          return True
      except Exception, e:
        p_err('[%s][is_excluded] %s' % (self.session_id, repr(e)))
        raise e
    return False

  def process_highlight(self, entry):

    if not self.highlight:
      return

    for key, highlights in self.highlight:
      try:
        # FIXME Dangerous
        value = eval('entry%s' % key)
        r_hl = re.compile(u'(' + u'|'.join(highlights) + u')', re.I | re.U)
        new_value = r_hl.sub(unicode(ANSI.fired) + ur'\1' + unicode(ANSI.freset), value)
        exec u'entry%s = u"""%s"""' % (key, new_value.replace(u'"', ur'\"'))
      except Exception, e:
        p_err('[%s] %s' % (self.session_id, repr(e)))
        raise e

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    if self.hide_id:
      msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id='*Source ID is Hidden*')
    else:
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
      if self.RE_INCLUDE and not self.is_included(entry):
        continue
      if self.is_excluded(entry):
        continue
      # XXX
      try:
        self.process_highlight(entry)
        print self.output(entry=entry, src_name=self.src_name, **common_tpl_opts)
        if hasattr(self, 'say'):
          self.sayit(self.say(entry=entry, src_name=self.src_name, **common_tpl_opts))
      except Exception, e:
        print entry
        raise e

  def sayit(self, text):

    # XXX !!!Experimental!!! Should have no quotation mark in text
    # TODO: Use pipe and/or speechd
    #os.system('echo "%s" | festival --tts &' % text.replace('"', ''))
    os.system('echo "%s" | festival --tts' % text.replace('"', ''))


class Twitter(Source):

  TYPE = 'twitter'
  REQUEST_URI = 'http://api.twitter.com/1/statuses/friends_timeline.json'

  def __init__(self, src):
    
    super(Twitter, self).__init__(src)
    
    self.username = src['username']
    self.consumer_key = src['consumer_key']
    self.consumer_secret = src['consumer_secret']
    
    self.src_id = self.username
    self.src_name = src.get('src_name', 'Twitter')
    self.interval = src.get('interval', 90)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(status["created_at"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!status["user"]["screen_name"]!@@!ansi.freset!@: @!unescape(status["text"])!@ @!ansi.fmagenta!@@!surl(status["tweet_link"])!@@!ansi.freset!@'), escape=None)

    self._init_session()
    self.create_connection()
    self._load_last_id()

  def create_connection(self):
    
    self.consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
    if 'access_token' not in self.session:
      self.get_access_token()
      
    self.token = oauth.Token(self.session['access_token']['oauth_token'],
        self.session['access_token']['oauth_token_secret'])
    self.client = oauth.Client(self.consumer, self.token)

    # Test if access token is working
    resp, content = self.client.request('https://api.twitter.com/1/account/verify_credentials.json', 'GET')
    if resp['status'] == '401':
      p_err('Something is wrong with access token, getting again...\n')
      self.get_access_token()
      self.token = oauth.Token(self.session['access_token']['oauth_token'],
          self.session['access_token']['oauth_token_secret'])
      self.client = oauth.Client(self.consumer, self.token)

  def get_access_token(self):

    p('\nGetting Access Token from Twitter...\n\n')

    client = oauth.Client(self.consumer)

# Step 1: Get a request token. This is a temporary token that is used for 
# having the user authorize an access token and to sign the request to obtain 
# said access token.

    resp, content = client.request(request_token_url, "GET")
    if resp['status'] != '200':
      p_err(repr(resp))
      p_err(repr(content))
      raise Exception("Invalid response %s." % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))

    p("Request Token:\n")
    p("    - oauth_token        = %s\n" % request_token['oauth_token'])
    p("    - oauth_token_secret = %s\n" % request_token['oauth_token_secret'])
    p('\n')

# Step 2: Redirect to the provider. Since this is a CLI script we do not 
# redirect. In a web application you would redirect the user to the URL
# below.

    p("Go to the following link in your browser:\n")
    p("%s?oauth_token=%s\n" % (authorize_url, request_token['oauth_token']))
    p('\n')

# After the user has granted access to you, the consumer, the provider will
# redirect you to whatever URL you have told them to redirect to. You can 
# usually define this in the oauth_callback argument as well.
    
    accepted = 'n'
    while accepted.lower() == 'n':
          accepted = raw_input('Have you authorized me? (y/n) ')
          oauth_verifier = raw_input('What is the PIN? ')

# Step 3: Once the consumer has redirected the user back to the oauth_callback
# URL you can request the access token the user has approved. You use the 
# request token to sign this request. After this is done you throw away the
# request token and use the access token returned. You should store this 
# access token somewhere safe, like a database, for future use.
    token = oauth.Token(request_token['oauth_token'],
        request_token['oauth_token_secret'])
    token.set_verifier(oauth_verifier)
    client = oauth.Client(self.consumer, token)

    resp, content = client.request(access_token_url, "POST")
    access_token = dict(urlparse.parse_qsl(content))
    
    p("Access Token:\n")
    p("    - oauth_token        = %s\n" % access_token['oauth_token'])
    p("    - oauth_token_secret = %s\n" % access_token['oauth_token_secret'])
    p('\n')
    p("You may now access protected resources using the access tokens above.\n" )
    p('\n')

    self.session['access_token'] = access_token
    self.access_token = access_token

  @staticmethod
  def to_localtime(d):

    return datetime(*fp._parse_date(d)[:6]).replace(tzinfo=utc).astimezone(local_tz)

  def get_list(self):

    request_uri = self.REQUEST_URI
    if self.last_id:
      request_uri += '?since_id=%s' % self.last_id
    try:
      resp, content = self.client.request(request_uri, 'GET')
      if resp['status'] != '200':
        p_err("Invalid response %s.\n" % resp['status'])
        return
      return json.loads(content)
    except AttributeError, e:
      if repr(e) == """AttributeError("'NoneType' object has no attribute 'makefile'",)""":
        # XXX http://code.google.com/p/httplib2/issues/detail?id=62
        # Force to reconnect
        p_err("AttributeError: 'NoneType' object has no attribute 'makefile'\n")
        self.create_connection()
        return
      else:
        raise e

  @safe_update
  def update(self):

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    statuses = self.get_list()
    p_clr(msg)

    if not statuses:
      return
    self._update_last_id(statuses[0]['id'])

    statuses.reverse()
    for status in statuses:
      p_dbg('ID: %s' % status['id'])
      if self.is_excluded(status):
        continue
      status['tweet_link'] = 'http://twitter.com/%s/status/%s' % (status['user']['screen_name'], status['id'])
      status['created_at'] = self.to_localtime(status['created_at'])
      self.process_highlight(status)
      print self.output(status=status, src_name=self.src_name, **common_tpl_opts)


# FIXME Merge into class Twitter
class TwitterMentions(Twitter):

  TYPE = 'twittermentions'
  REQUEST_URI = 'http://api.twitter.com/1/statuses/mentions.json'

  def __init__(self, src):
    
    super(Twitter, self).__init__(src)
    
    self.username = src['username']
    self.consumer_key = src['consumer_key']
    self.consumer_secret = src['consumer_secret']
    
    self.src_id = self.username
    self.src_name = src.get('src_name', 'TwitterMentions')
    self.interval = src.get('interval', 90)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(status["created_at"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!status["user"]["screen_name"]!@@!ansi.freset!@: @!unescape(status["text"])!@ @!ansi.fmagenta!@@!surl(status["tweet_link"])!@@!ansi.freset!@'), escape=None)

    self._init_session()
    self.create_connection()
    self._load_last_id()


class FriendFeed(Source):

  TYPE = 'friendfeed'

  def __init__(self, src):

    super(FriendFeed, self).__init__(src)
    
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

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    if not self.token:
      self.token = self.api.fetch_updates()['update']['token']

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
    
    super(Feed, self).__init__(src)
    
    self.feed = src['feed']
    # Used as key to store session data
    self.src_id = self.feed
    self.src_name = src.get('src_name', 'Feed')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry.link)!@@!ansi.fmagenta!@@!ansi.freset!@@!ansi.freset!@'), escape=None)
    # XXX
    if 'say' in src:
      self.say = tpl(src['say'])

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


class Craigslist(Feed):

  TYPE = 'cl'
  ID_RE = re.compile('.*?(\d+)\.html')

  def __init__(self, src):
    
    super(Feed, self).__init__(src)
    
    self.feed = src['feed']
    # Used as key to store session data
    self.src_id = self.feed
    self.src_name = src.get('src_name', self.TYPE)
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry.link)!@@!ansi.fmagenta!@@!ansi.freset!@@!ansi.freset!@'), escape=None)
    # XXX
    if 'say' in src:
      self.say = tpl(src['say'])

    self._init_session()
    self._load_check_list()
    if isinstance(self.check_list, dict):
      self.check_list = 0
    # Use it to store check_list for comparison of a list of entries
    self._check_list = None

  def _update_check_list(self):
    # It is not a list but a single int
    self._check_list = None
    self.session['check_list'] = self.check_list
    session[self.session_id] = self.session
    p_dbg('Updated [%s] check_list' % self.session_id)

  @classmethod
  def get_entry_id(cls, entry):

    m = cls.ID_RE.match(entry['guid'])
    if not m:
      raise ValueError('Craiglist should have guid')

    return int(m.group(1))

  def is_new_item(self, entry):
    '''Check if entry is new and also update check_list if it is new'''
    e_id = self.get_entry_id(entry)
    if self._check_list is None:
      self._check_list = self.check_list
    if e_id > self._check_list:
      if e_id > self.check_list:
        self.check_list = e_id
      return True
    return False

  def get_list(self):

    feed = super(Craigslist, self).get_list()

    new_entries = []
    for entry in feed['entries']:
      # Some entries didn't have updated or published, they are very old
      # entries, need to be filtered out.
      if entry.published:
        new_entries.append(entry)

    feed['entries'] = new_entries
    return feed


class FlickrContacts(Craigslist):

  TYPE = 'frck'

  @classmethod
  def get_entry_id(cls, entry):

    return super(Feed, cls).get_entry_id(entry)


class StackOverflowNewOnly(Craigslist):

  TYPE = 'sono'
  ID_RE = re.compile('.*?(\d+)/[a-zA-Z0-9-]+')

  @classmethod
  def get_entry_id(cls, entry):

    m = cls.ID_RE.match(entry['id'])
    if not m:
      raise ValueError('StackOverflow should have guid')

    return int(m.group(1))


class TwitterSearch(Feed):

  TYPE = 'twittersearch'
  SEARCH_URL = 'http://search.twitter.com/search.atom'
  # For reseting only
  PUBLIC_URL = 'http://twitter.com/statuses/public_timeline.json'
  RE_LINK = re.compile(u'(.*?)<a href="(.*?)">(.*?)</a>(.*)', re.DOTALL)

  def __init__(self, src):
    
    # Skip feed
    super(Feed, self).__init__(src)

    self.src_name = src.get('src_name', 'TwitterSearch')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["published"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["author"]["screen_name"]!@@!ansi.freset!@: @!remove_additional_space(entry["title"])!@ @!ansi.fmagenta!@@!surl(entry["link"])!@@!ansi.freset!@'), escape=None)
    self.q = src['q']
    self.lang = src.get('lang', 'en')
    self.src_id = '%s:%s' % (self.lang, self.q)
    self.rpp = src.get('rpp', 15)

    self._init_session()
    # Do not load last_id, so we can have a clean-run searching
    # self._load_last_id()
    self.last_id = None
    self.update(suppress=True)
 
  def get_list(self):

    parameters = {'q': self.q, 'lang': self.lang, 'rpp': self.rpp, 'result_type': 'recent'}
    if self.last_id:
      parameters['since_id'] = self.last_id
    feed = fp.parse(self.SEARCH_URL + '?' + urllib.urlencode(parameters))
    try:
      if 'status' not in feed:
        p_err('No key status in feed: %s\n' % feed['bozo_exception'])
        return
      if feed['status'] == 403 or feed['status'] == 404:
        p_err('Got 403 or 404\n')
        return
      elif feed['status'] == 503:
        p_err('HTTP Status 503\n')
        return
    except AttributeError, e:
      p_dbg(repr(feed))
      raise e

    if not feed['feed']:
      # The feed (since_id) is expired, feed.entries is [], so just return
      return feed
    # XXX
    try:
      for link in feed.feed.links:
        if link.rel == 'refresh':
          self._update_last_id(link.href.rsplit('=', 1)[1])
          break
    except AttributeError, e:
      print feed
      raise e

    new_entries = []
    for entry in feed['entries']:
      screen_name, name = entry['author'].split(' ', 1)
      entry['author'] = {'screen_name': screen_name, 'name': name[1:-1]}
      if self.is_excluded(entry):
        continue
      new_entries += [entry]
    feed['entries'] = new_entries

    return feed

  @safe_update
  def update(self, suppress=False):
    # suppress is for first seach of session, user may not want to read lots of
    # tweets when they just run clis.py

    if time.time() < self.interval + self.last_accessed:
      return
    self.last_accessed = time.time()

    msg = self.TPL_ACCESS(ansi=ANSI, src_name=self.src_name, src_id=self.src_id)
    p(msg)
    feed = self.get_list()
    if feed is None:
      return
    p_clr(msg)
    if suppress:
      return

    if not feed['entries']:
      return
      
    entries = feed['entries']
    # Get entries after last_id
    for entry in entries:
      self.datetimeize(entry)

    entries.reverse()
    for entry in entries:
      p_dbg('ID: %s' % self.get_entry_id(entry))
      # XXX make this a method and move to base class, and also should support re
      if self.is_excluded(entry):
        continue
      self.process_highlight(entry)
      print self.output(entry=entry, src_name=self.src_name, **common_tpl_opts)


# http://stackoverflow.com/questions/52880/google-reader-api-unread-count
class GoogleBase(Feed):

  def __init__(self, src):
    
    # Skip Feed
    super(Feed, self).__init__(src)

    auth_url = 'https://www.google.com/accounts/ClientLogin'
    self.email = src['email']
    auth_req_data = urllib.urlencode({
        'accountType': 'GOOGLE',
        'Email': self.email,
        'Passwd': src['password'],
        'service': 'reader',
        'source': 'YJL-clis-0',
        })
    auth_req = urllib2.Request(auth_url, data=auth_req_data)
    auth_resp = urllib2.urlopen(auth_req)
    auth_resp_content = auth_resp.read()
    p_dbg(auth_resp_content)
    auth_resp_dict = dict(x.split('=') for x in auth_resp_content.split('\n') if x)
    p_dbg(auth_resp_dict)
    self.Auth = auth_resp_dict["Auth"]

  def get(self, url, header=None):

    if header is None:
      header = {}

    header['Authorization'] = 'GoogleLogin auth=%s' % self.Auth

    req = urllib2.Request(url, None, header)
    f = urllib2.urlopen(req)
    content = f.read()
    f.close()
    return content


class GoogleMail(Feed):

  TYPE = 'gmail'

  def __init__(self, src):
   
    # Skip Feed
    super(Feed, self).__init__(src)
    
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
  # Google Reader has this attribute to entry entitiy, this is a reliable
  # source to check if item is new.
  RE_CRAWL_TIME = re.compile(r'gr:crawl-timestamp-msec="(\d+)"')

  def __init__(self, src):
    
    super(GoogleReader, self).__init__(src)

    self.src_id = self.email
    self.src_name = src.get('src_name', 'GR')
    self.interval = src.get('interval', 60)
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["source"]["title"]!@@!ansi.freset!@: @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry["link"])!@@!ansi.freset!@'), escape=None)
    
    self._init_session()
    self._load_check_list()

  def get_list(self):
    '''Retrieve Google Reader feed, and replace published date with crawl
    time'''
    # Get the last 50 items
    content = self.get('http://www.google.com/reader/atom/user%2F-%2Fstate%2Fcom.google%2Freading-list?n=50')
    feed = fp.parse(content)
    # TODO use last_id with this crawl_times, no need to use long check_list
    crawl_times = self.RE_CRAWL_TIME.findall(content)
    if len(crawl_times) != len(feed.entries):
      p_err('Lengths did not match, crawl times are not processed.')
      return feed
   
    for i in xrange(len(crawl_times)):
      feed.entries[i].published_parsed = datetime.utcfromtimestamp(float(crawl_times[i]) / 1000.0).timetuple()
    
    # remove read items
    entries = []
    for entry in feed.entries:
      if not [True for category in entry.categories if category[1].endswith('/state/com.google/read')]:
        entries.append(entry)
    feed.entries = entries
    return feed


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

    super(Weather, self).__init__(src)

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


class PunBB12OnlyNew(PunBB12, Craigslist):

  TYPE = 'punbb12onlynew'
  ID_RE = re.compile(r'.*?viewtopic\.php\?id=(\d+)')

  @classmethod
  def get_entry_id(cls, entry):

    m = cls.ID_RE.match(entry['link'])
    if not m:
      raise ValueError('Punbb should have link')

    return int(m.group(1))


class Tail(Source):

  TYPE = 'tail'
  # How many lines printed in one update()
  MAX_LINES = 100

  def __init__(self, src):
    
    super(Tail, self).__init__(src)

    self.filename = path.expanduser(src['file'])
    self.src_id = self.filename
    self.src_name = src.get('src_name', 'Tail')
    self.output = tpl(src.get('output', '@!ansi.fgreen!@@!ftime(line["date"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!line["text"]!@'), escape=None)

    self.openfile(src.get('last_lines', 0))

  def __del__(self):

    self.f.close()

  def openfile(self, last_lines=0):

    try:
      self.f = open(self.src_id, 'r')
      if last_lines:
        self.f.seek(-last_lines, os.SEEK_END)
      self.fstat = os.stat(self.filename)[stat.ST_INO:stat.ST_DEV + 1]
      p_dbg('[%s] file opened' % self.src_id)
    except IOError:
      p_dbg('[%s] Unable to open file' % self.src_id)
      self.f = None
      self.fstat = None
      return False
    return True

  @safe_update
  def update(self):

    try:
      fstat = os.stat(self.filename)[stat.ST_INO:stat.ST_DEV + 1]
    except OSError:
      return

    if fstat != self.fstat:
      # File has been recreated
      if not self.openfile():
        # Failed to open
        return

    i = self.MAX_LINES
    while i:
      line = self.f.readline()
      if not line:
        break
      p(self.output(line={'date': datetime.now(), 'text': line}, src_name=self.src_name, **common_tpl_opts))
      i -= 1


SOURCE_CLASSES = {'twitter': Twitter, 'twittermentions': TwitterMentions,
    'friendfeed': FriendFeed, 'feed': Feed,
    'sono': StackOverflowNewOnly, 'cl': Craigslist, 'frck': FlickrContacts,
    'gmail': GoogleMail, 'greader': GoogleReader, 'weather': Weather,
    'punbb12': PunBB12, 'punbb12onlynew': PunBB12OnlyNew,
    'twittersearch': TwitterSearch, 'tail': Tail}

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

def load_config():
  
  global options

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

  return sources, cfg

######
# Main

def main():

  global fd, old_settings, p_stdin
  global options, session, width

  p('''clis (C) 2009, 2010 Yu-Jie Lin
The code is licensed under the terms of the GNU General Public License (GPL).

For running the code, you must agree with all limitations which are denoted in
clis_cfg-sample.py, read the file for more information.\n\n''')

  # Process arguments
  options, args = parser_args()
  
  sources, cfg = load_config()
  
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
  not_quit = True
  while not_quit:
    try:
      for src in sources:
        src.update()
        if getch() == "\x0d":
          sys.stdout = sys.__stdout__
          sys.stderr = sys.__stderr__
          termios.tcsetattr(fd, termios.TCSANOW, old_settings)
          p('\033[?25h')
          cmd = raw_input('Command > ')
          p('\033[?25l')
          tty.setraw(fd)
          sys.stdout = STDOUT_R
          sys.stderr = STDERR_R
          cmd = re.sub('\W', '', cmd)
          if cmd == 'reload':
            session.close()
            sources, cfg = load_config()
            del cfg
            p('Configuration reloaded.\n')
          elif cmd == 'clear':
            # Clear screen
            p('\033[2J\033[H')
          elif cmd == 'quit':
            not_quit = False
            break
          elif cmd == "":
            # Entry key
            p('\033[A\033[97;101m' + u'─' * width + '\n\033[39;49m')
      session.do_sync(sources)
    except select.error:
      # Conflict with signal
      # select.error: (4, 'Interrupted system call') on p.poll(1)
      pass
  session.do_sync(sources)


if __name__ == '__main__':

  fd = None
  old_settings = None
  
  try:
    main()
  except Exception, e:
    sigexit(None, None)
    traceback.print_exc()
    raise e
  p('Bye!\n')
  sigexit(None, None)
