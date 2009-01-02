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


from datetime import datetime

from google.appengine.api import memcache


def incr(key):
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
  count = memcache.get('simple24_%s_total' % key)
  if count is None:
    return full_count(key)
  return count


def full_count(key):
  total_count = 0
  for hour in range(24):
    count = memcache.get('simple24_%s_%d' % (key, hour))
    if count is not None:
      total_count += count
  memcache.set('simple24_%s_total' % key, total_count)
  return total_count
