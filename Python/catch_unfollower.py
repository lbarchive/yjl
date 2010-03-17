#!/usr/bin/env python


import datetime as dt
import json
import os
import shelve
import urllib2


SCREEN_NAME = 'lyjl'
STATUSES_FOLLOWERS = 'http://twitter.com/statuses/followers/%s.json' % SCREEN_NAME
# Over this amount would limit to one record for a day.
RECORDS_THROTTLE = 30

def main():
  
  DIRNAME = os.path.expanduser('~/cron.gen')
  if not os.path.exists(DIRNAME):
    os.makedirs(DIRNAME)

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
    log = open(os.path.expanduser('~/cron.gen/cu_%s' % now.strftime('%Y%m%d-%H%M%S')), 'w')
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

  # Clean up
  for id in followers:
    fler = followers[id]
    if len(fler) < RECORDS_THROTTLE:
      continue
    # Need to remove some records
    new_records = []
    year = month = day = 0
    for record in fler:
      r_time = record['time']
      if r_time.year == year and r_time.month == month and r_time.day == day:
        continue
      year = r_time.year
      month = r_time.month
      day = r_time.day
      new_records.append(record)
    followers[id] = new_records

  s['followers'] = followers
  s.close()

if __name__ == '__main__':
  main()
