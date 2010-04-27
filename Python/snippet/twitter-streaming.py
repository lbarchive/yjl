#!/usr/bin/env python
# The MIT License
# 
# Copyright (c) 2010 Yu-Jie Lin
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import base64
import getpass
import json
import urllib
import urllib2
import time


def fetch(uri, username='', password='', data=None):
  
  headers = {}
  if username and password:
    headers['Authorization'] = 'Basic ' + base64.b64encode('%s:%s' % (username,
        password))
    headers['User-Agent'] = 'TwitterStreamingSample'
  
  req = urllib2.Request(uri, headers=headers)
  if data:
    req.add_data(urllib.urlencode(data))
  f = urllib2.urlopen(req)
  return f


def main():

  username = raw_input('Twitter Username: ')
  password = getpass.getpass('Twitter Password: ')
  track = raw_input('Tracking keyword? ')
  print

  try:
    f = fetch('http://stream.twitter.com/1/statuses/filter.json', username,
        password, {'track': track})
    print 'Tracking... [Control + C to stop]'
    print
    while True:
      line = f.readline()
      if line:
        status = json.loads(line)
        try:
          print '%s: %s' % (status['user']['screen_name'], status['text'])
        except KeyError, e:
          # Something we don't handle yet.
          print '* FIXME *', line
      else:
        time.sleep(0.1)
  except urllib2.HTTPError, e:
    # Deal with unexpected disconnection
    raise e
  except KeyboardInterrupt:
    # End
    f.close()
    print 'Bye!'


if __name__ == '__main__':
  main()
