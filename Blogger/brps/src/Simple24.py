# Simple24: Provides 24 hourly moving windows simple counting statistics
#
# Copyright (C) 2009 Yu-Jie Lin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Provides 24 hourly moving windows simple counting statistics."""


from datetime import datetime

from google.appengine.api import memcache


def incr(key):
  """Increases counter by one"""
  curr_hour = datetime.utcnow().hour
  idx_hour = memcache.get('simple24_%s_index' % key)
  if idx_hour != curr_hour:
    # Hour changes
    memcache.set('simple24_%s_index' % key, curr_hour)
    memcache.set('simple24_%s_%d' % (key, curr_hour), 1)
    # Do a full count
    full_count(key)
  else:
    if memcache.incr('simple24_%s_%d' % (key, curr_hour)) is None:
      memcache.set('simple24_%s_%d' % (key, curr_hour), 1)
    if memcache.incr('simple24_%s_total' % key) is None:
      full_count(key)


def get_count(key):
  """Returns the counter"""
  count = memcache.get('simple24_%s_total' % key)
  if count is None:
    return full_count(key)
  return count


def full_count(key):
  """Returns sum of all 24 counters"""
  total_count = 0
  for hour in range(24):
    count = memcache.get('simple24_%s_%d' % (key, hour))
    if count is not None:
      total_count += count
  memcache.set('simple24_%s_total' % key, total_count)
  return total_count


def get_hourly_counts(key):
  """Returns 24 counters"""
  counts = []
  for hour in range(24):
    count = memcache.get('simple24_%s_%d' % (key, hour))
    if count is None:
      counts.append(0)
    else:
      counts.append(count)
  return counts


def get_chart_uri(key, cache_time=300):
  """Returns a image URI of Google Chart API"""
  if cache_time > 0:
    chart_uri =  memcache.get('simple24_%s_chart_uri' % key)
    if chart_uri:
      return chart_uri
  curr_hour = datetime.utcnow().hour
  counts = get_hourly_counts(key)
  max_count = max(counts)
  min_count = max_count - int((max_count - min(counts)) / 0.95)
  if min_count < 0:
    min_count = 0

  # Rearrange counts from oldest to recent
  s_counts = [str(counts[(curr_hour + i + 1) % 24]) for i in range(24)]
  
  chtt = 'Completed request in 24-hour moving window|Times in UTC'
  chxt = 't,x,x,y'
  chxl = '0:|23 Hours ago' + '|'*11 +'12 Hours ago' + '|'*12 + 'This hour|'
  chxl += '1:|%s|' % '|'.join(s_counts)
  chxl += '2:|%s|' % '|'.join(
      [str((curr_hour + i + 1) % 24) for i in range(24)])
  chxl += '3:|%s' % '|'.join([str(min_count), str((min_count + max_count) / 2),
      str(max_count)])
  chd = ','.join(s_counts)
  chart_uri = "http://chart.apis.google.com/chart?chs=600x200&chf=bg,s,F5EDE3&\
chtt=%s&cht=bvs&chco=4D89F9&chbh=a&chd=t:%s&chds=%d,%d&chxt=%s&chxl=%s" % \
      (chtt, chd, min_count, max_count, chxt, chxl)
  if cache_time > 0:
    memcache.set('simple24_%s_chart_uri' % key, chart_uri, cache_time)
  return chart_uri
