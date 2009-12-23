#!/usr/bin/env python
# Use http://tweetbackup.com/ Text export file to generate a file which you can
# input into Wordle.net Advanced http://www.wordle.net/advanced
#
# Usage: ./tweets_word.py export.txt

import operator
import re
import sys

cw = ['rt']
try:
  for line in file('common.txt', 'r'):
    cw.append(line.replace('\n', '').lower())
except:
  pass

RE_DATE = re.compile('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\r\n')
RE_WORD_SPLITTER = re.compile('[^\'@a-zA-Z0-9_]+')
RE_TWEET = re.compile('[_a-zA-Z0-9]+: (.*)')
# Not really good one, but acceptable
RE_URL = re.compile('(ht|f)tps?\://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,3}(/\S*)?')

words = {}
try:
  f = open(sys.argv[1], 'r')
  f.readline()
  f.readline()
  f.readline()

  for line in f:
    if RE_DATE.match(line) or line == '\r\n':
      continue
    m = RE_TWEET.match(line);
    if m:
      line = m.group(1)
    line = RE_URL.sub(' ', line)
    for w in RE_WORD_SPLITTER.split(line.rstrip('\r\n').lower()):
      if not w or w in cw:
        continue
      if w in words:
        words[w] += 1
      else:
        words[w] = 1
finally:
  f.close()

words = words.items()
words.sort(key=operator.itemgetter(1))
words = words[-500:]

for word, count in words:
  print '%s: %d' % (word, count)
