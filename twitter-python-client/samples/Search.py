#!/usr/bin/python


import time

import twitter_client as tc
import twitter_client.service

client = twitter_client.service.TwitterService(application_name='TwitterClientSample/0')
search = client.NewSearch()
search.keywords = ['twitter']
search.show_user = True

print
print 'Searching...'
print

feed = search.Search()
for entry in feed.entry:
  print entry.published.text + ':', entry.title.text

print
print 'Waiting for 5 seconds to refresh...'
print
time.sleep(5)

feed = search.Refresh()

for entry in feed.entry:
  print entry.published.text + ':', entry.title.text

