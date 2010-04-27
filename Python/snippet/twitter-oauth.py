#!/usr/bin/env python
# The MIT License
# 
# Copyright (c) 2010 Yu-Jie Lin
# Copyright (c) 2007 Leah Culver
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
#
# Create a config.py file at current directory with such content
# consumer_key = 'my_key_from_twitter'
# consumer_secret = 'my_secret_from_twitter'


import json
import urllib
import urlparse
import sys

import oauth2 as oauth


def wrong_config():

  global config
  class Config():
    pass
  config = Config()
  config.__dict__['consumer_key'] = raw_input('Consumer key? ')
  config.__dict__['consumer_secret'] = raw_input('Consumer secret? ')

# Load oauth key, token and secret
try:
  import config
except ImportError:
  wrong_config()

if not hasattr(config, 'consumer_key') or not hasattr(config, 'consumer_secret'):
  wrong_config()

request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
authorize_url = 'https://api.twitter.com/oauth/authorize'


def get_access_token(consumer):

  client = oauth.Client(consumer)

# Step 1: Get a request token. This is a temporary token that is used for 
# having the user authorize an access token and to sign the request to obtain 
# said access token.

  resp, content = client.request(request_token_url, "GET")
  if resp['status'] != '200':
      raise Exception("Invalid response %s." % resp['status'])

  request_token = dict(urlparse.parse_qsl(content))

  print "Request Token:"
  print "    - oauth_token        = %s" % request_token['oauth_token']
  print "    - oauth_token_secret = %s" % request_token['oauth_token_secret']
  print 

# Step 2: Redirect to the provider. Since this is a CLI script we do not 
# redirect. In a web application you would redirect the user to the URL
# below.

  print "Go to the following link in your browser:"
  print "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
  print 

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
  client = oauth.Client(consumer, token)

  resp, content = client.request(access_token_url, "POST")
  access_token = dict(urlparse.parse_qsl(content))

  print "Access Token:"
  print "    - oauth_token        = %s" % access_token['oauth_token']
  print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']
  print
  print "You may now access protected resources using the access tokens above." 
  print

  return access_token


def main():

  consumer = oauth.Consumer(config.consumer_key, config.consumer_secret)

  # Check if we have access_token
  if not hasattr(config, 'access_token'):
    config.access_token = get_access_token(consumer)
    # XXX save token, this is not a good way, I'm too lazy to use something
    # like shelve.
    f = open('config.py', 'w')
    f.write('consumer_key = %s\n' % repr(config.consumer_key))
    f.write('consumer_secret = %s\n' % repr(config.consumer_secret))
    f.write('access_token = %s\n' % repr(config.access_token))
    f.close()
    print '\n\nconfig.py written.\n\n'

  token = oauth.Token(config.access_token['oauth_token'],
      config.access_token['oauth_token_secret'])
  client = oauth.Client(consumer, token)

  while True:
    # Show the menu
    print '''1) Show friends timeline
2) Post update
Q) Exit
'''

    choice = raw_input('Choice? ').lower()
    print
    if choice == '1':
      request_uri = 'https://api.twitter.com/1/statuses/friends_timeline.json'
      resp, content = client.request(request_uri, 'GET')
      if resp['status'] != '200':
        print repr(resp)
        print
        print repr(content)
        print
        print "Invalid response %s." % resp['status']
        print
        continue
      statuses = json.loads(content)
      for status in statuses:
        print '%s: %s' % (status['user']['screen_name'], status['text'])
      print
    elif choice == '2':
      request_uri = 'https://api.twitter.com/1/statuses/update.json'
      # TODO Length check
      data = {'status': raw_input("What's happening? ")}
      # See http://code.google.com/p/httplib2/wiki/Examples#Forms for httplib2
      # form data sending
      resp, content = client.request(request_uri, 'POST',
          urllib.urlencode(data))
      if resp['status'] != '200':
        print repr(resp)
        print
        print repr(content)
        print
        print "Invalid response %s." % resp['status']
        print
        continue
      status = json.loads(content)
      print 'See your tweet at http://twitter.com/%s/status/%d' % (
          status['user']['screen_name'], status['id'])
    elif choice == 'q':
      break
    print


if __name__ == '__main__':
  main()
