#!/usr/bin/env python


import datetime as dt
import json
import os
import shelve
import urllib2


SCREEN_NAME = 'lyjl'
STATUSES_FOLLOWERS = 'http://twitter.com/statuses/followers/%s.json' % SCREEN_NAME


def main():

  # Get the list
  u = urllib2.urlopen(STATUSES_FOLLOWERS)
  now = dt.datetime.now()
  raw = u.read()
  u.close()

  flers = {}
  for fler in json.loads(raw):
    new_fler = {}
    for key in ['id', 'screen_name', 'followers_count', 'friends_count', 'statuses_count']:
      new_fler[key] = fler[key]
    new_fler['time'] = now
    flers[fler['id']] = new_fler

  if not flers:
    # No followers, just leave (how come no followers?)
    return

  # Open shelve
  s = shelve.open(os.path.expanduser('~/.catch_unfollower'))
  if 'followers' in s:
    followers = s['followers']
  else:
    followers = {}

  # Find un-followers
  unfollower_ids = set(followers.keys()) - set(flers.keys())

  # Add new followers and update counts if change
  for id in flers:
    if id in followers:
      # Existing follower
      last = followers[id][-1]
      changed = False
      for key in ['screen_name', 'friends_count']:
        if last[key] != flers[id][key]:
          changed = True
          break

      if changed:
        fler = followers[id]
        fler.append(flers[id])
    else:
      # New follower
      followers[id] = [flers[id]]

  if unfollower_ids:
    log = open(os.path.expanduser('~/cu_%s' % now.strftime('%Y%m%d-%H%M%S')), 'w')
    # Print unfollowers
    for id in unfollower_ids:
      fler = followers[id]
      print >> log, '@%s: %s - http://twitter.com/%s' % (fler[-1]['screen_name'],
          fler[-1]['time'] - fler[0]['time'], fler[-1]['screen_name'])
      for r in fler:
        print >> log, '  %s: % 5d/% 5d/% 5d' % (r['time'], r['friends_count'],
            r['followers_count'], r['statuses_count'])
      print >> log
      del followers[id]
    log.close()

  s['followers'] = followers
  s.close()

if __name__ == '__main__':
  main()
