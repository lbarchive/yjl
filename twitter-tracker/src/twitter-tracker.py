#!/usr/bin/python


import os
import readline
import time

import twitter_client as tc
import twitter_client.service


histfile = os.path.join(os.environ['HOME'], '.tthist')
try:
    readline.read_history_file(histfile)
except IOError:
    pass
import atexit
atexit.register(readline.write_history_file, histfile)
del os, histfile

query =  raw_input('Please input query: ')

client = twitter_client.service.TwitterService(application_name='TwitterClientSampleTracker/0')
search = client.NewSearch()
# TODO Use _ParseQueryString
search.keywords = query.split(' ')
search.show_user = True

print
print 'Searching...'

feed = search.Search()
try:
  while True:
    if feed.entry:
      feed.entry.reverse()
      print
    for entry in feed.entry:
      print entry.published.text + ':', #entry.title.text
      print entry.content.text.replace('<b>', '\033[1;31m').replace('</b>', '\033[0m')
    time.sleep(60)
    feed = search.Refresh()
except KeyboardInterrupt:
  print
  print
  print "Seems that you have read enough, bye!"
  print
