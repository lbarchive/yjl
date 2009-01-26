# LasTweet lists last tweets to friends
# Copyright (C) 2008  Yu-Jie Lin
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Provides utilities for BRPS"""


import base64
import datetime
import logging

from google.appengine.api import urlfetch 


def td_seconds(t):
  """Returns timedelta of now to t in seconds"""
  td = (datetime.datetime.utcnow() - t)
  return td.days * 86400 + td.seconds + td.microseconds / 1000000.0


def now(utc=True):
  """Returns UTC time if utc, otherwise local time"""
  if utc:
    return datetime.datetime.utcnow()
  return datetime.datetime.now()

def fetch(uri, username='', password=''):
  """Can fetch with Basic Authentication"""
  headers = {}
  if username and password:
    headers['Authorization'] = 'Basic ' + base64.b64encode('%s:%s' % \
        (username, password))
  
  f = urlfetch.fetch(uri, headers=headers)
  logging.debug('Fetching %s (%s): %d' % (uri, username, f.status_code))
  return f
