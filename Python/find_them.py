#!/usr/bin/env python
# Fine people on websites using Twitter's following list


from optparse import OptionParser

import json
import Queue
import random
import socket
import threading
import time
import urllib2
socket.setdefaulttimeout(10)


__author__ = 'Yu-Jie Lin'
__copyright__ = "Copyright 2010, Yu-Jie Lin"
__credits__ = []
__license__ = "New BSD"
__version__ = '0.0.0.1'
__email__ = 'livibetter@gmail.com'
__status__ = 'Development'


urls = [
    'http://www.google.com/profiles/%s',
    ('http://%s.mp/', 'redirect'),
    ('http://flavors.me/%s', 'Oops! Looks like there was an error. If this issue persists, please'),

    'http://%s.blogspot.com/',
    ('http://%s.wordpress.com/', 'redirect'),
    ('http://%s.posterous.com/', 'redirect'),
    
    'http://%s.livejournal.com/',
    'http://%s.skyrock.com/profil/',
    'http://%s.tumblr.com/',

    'http://delicious.com/%s',
    ('http://www.diigo.com/user/%s', "This account doesn't exist or has been marked as spammer and removed."),
    'http://www.mister-wong.com/user/%s/',
    ('http://www.stumbleupon.com/stumbler/%s/', 'no such username'),
    'http://www.twine.com/user/%s',

    ('http://www.librarything.com/profile/%s', "Error: This user doesn't exist"),

    ('http://digg.com/users/%s', 'redirect'),
    'http://www.reddit.com/user/%s',

    'http://www.flickr.com/photos/%s/',
    'http://www.fotolog.com/%s',
    ('http://media.photobucket.com/users/%s', ''),
    'http://picasaweb.google.com/%s',
    ('http://%s.smugmug.com/', 'Learn more'),
    'http://www.zooomr.com/people/%s/',
    'http://%s.deviantart.com/',
    ('http://dailybooth.com/%s', 'You are attempting to view an invalid user.'),

    'http://www.facebook.com/%s',
    'http://identi.ca/%s',
    ('http://www.plurk.com/%s', 'is not found'),

    'http://www.ilike.com/user/%s',
    'http://www.last.fm/user/%s',
    ('http://www.pandora.com/people/%s', 'User not found'),

    'http://www.backtype.com/%s',
    'http://disqus.com/%s/',
    ('http://intensedebate.com/people/%s', 'Invalid user name'),

    ('http://12seconds.tv/channel/%s', 'redirect'),
    'http://www.dailymotion.com/%s',
    ('http://vimeo.com/%s', ''),
    ('http://www.youtube.com/user/%s', 'redirect'),
    ('http://%s.blip.tv/', "I couldn't find that user"),
    
    'http://www.netvibes.com/%s',
    ('http://www.slideshare.net/%s', 'redirect'),
    'http://wakoopa.com/%s',

    ('http://www.myspace.com/%s', 'ctl00_ctl00_cpMain_cpMain_Unavailable1_ErrorMessageLabel'),

    'http://friendfeed.com/%s',
    ('http://foursquare.com/user/%s', 'redirect'),
    ]


class HeadRequest(urllib2.Request):

  def get_method(self):

    return 'HEAD'


def check_url(url, method, retry=3):
  
  try:
    if isinstance(method, str) and method != 'redirect':
      # method is a string
      if 'vimeo' in url:
        USERAGENT = 'FindMore/0.0.0.1'
        HEADERS = {'User-Agent': USERAGENT}

        req = urllib2.Request(url, headers=HEADERS)
        f = urllib2.urlopen(req)
      else:
        f = urllib2.urlopen(url)
      
      content = f.read()
      f.close()
      if content == '' or (method != '' and method in content):
        return
    else:
      response = urllib2.urlopen(HeadRequest(url))
      if method == 'redirect' and response.geturl() != url:
        return
    return url
  except (urllib2.HTTPError, urllib2.URLError), e:
    if retry > 0:
      time.sleep(1)
      check_url(url, method, retry - 1)
    else:
      return '%s %s' % (url, repr(e))


MAX_CHECKERS = 20
checking_queue = Queue.Queue()


def checker():

  while True:

    username = checking_queue.get()
    results = []
    for item in urls:
      if isinstance(item, tuple):
        url = item[0]
        method = item[1]
      else:
        url = item
        method = None
      # Don't rush
      time.sleep(random.random() / 2)
      results.append(check_url(url % username, method))

    print username
    for result in results:
      if result:
        print ' >', result
    print

    checking_queue.task_done()


for i in range(MAX_CHECKERS):
  c = threading.Thread(target=checker)
  c.setDaemon(True)
  c.start()


def main():

  usage = 'usage: %prog [options] [username]'
  parser = OptionParser(usage=usage, version='%%prog %s' % __version__)
  parser.add_option('-a', '--additional',
      type='str', dest='additional',
      help='Also check these users, e.g. "-a user1,user2,user3"',
      )
  options, args = parser.parse_args()

  if len(args) > 1:
    parser.error('Can only accept one username')
  
  if len(args) == 1:
    f = urllib2.urlopen('http://api.twitter.com/1/statuses/friends/%s.json' % args[0])
    j = json.loads(f.read())
    f.close()

    for user in j:
      username = user['screen_name']
      checking_queue.put(username)

  if options.additional:
    for u in options.additional.split(','):
      checking_queue.put(u)

  checking_queue.join()


if __name__ == '__main__':
  main()
