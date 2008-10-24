#!/usr/bin/python


import twitter_client as tc
import twitter_client.service

client = twitter_client.service.TwitterService()

feed = client.Search('twitter')

print
print 'Searching...'
print

for entry in feed.entry:
  print entry.title.text
