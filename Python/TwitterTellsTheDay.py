#!/usr/bin/python
# Using Twitter to find out how special today is
#
# This code is in Public Domain.
#
# Author:
#  2009 Yu-Jie Lin


from sys import exit
from urllib import urlopen
import simplejson as json


TREND_API = 'http://search.twitter.com/trends/current.json'


f = urlopen(TREND_API)
if f.info()['status'] == '200 OK':
  _, trends = json.loads(f.read())['trends'].popitem()
  for t in trends:
    if 'day' in t['name'] or 'Day' in t['name']:
      print t['name'].replace('Happy', '').replace('happy', '').replace('#', '').strip()
else:
  print 'Unable to retrieve, status code: %s' % f.info()['status']
  exit(1)
