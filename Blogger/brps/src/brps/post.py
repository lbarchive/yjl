# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
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


import logging
import sets
import simplejson as json
import urllib

from google.appengine.api import memcache
from google.appengine.api import urlfetch 
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from brps import util


# Since Google hasn't support disjunction querying on labels
# Need to limit the max queries
MAX_LABEL_QUERIES = 5
MAX_POSTS = 10
# Post cache time in seconds
POST_CACHE_TIME = 3600
LABEL_QUERY_RESULT_CACHE_TIME = 86400
# In seconds
UPDATE_INTERVAL = 86400


POST_FETCH_URL = 'http://www.blogger.com/feeds/%d/posts/default/%d?alt=json'
POST_QUERY_URL = 'http://www.blogger.com/feeds/%d/posts/default?category=%s&max-results=100&alt=json'


class Post(db.Model):
  blog_id = db.IntegerProperty()
  post_id = db.IntegerProperty()
  last_updated = db.DateTimeProperty()
  relates = db.TextProperty()

  def _get_relates(self):
    if self.relates:
      return json.loads(self.relates.encode('latin-1'))

  def _set_relates(self, new_relates):
    if isinstance(new_relates, (str, unicode)):
      self.relates = new_relates
    else:
      self.relates = db.Text(json.dumps(new_relates), encoding='latin-1')

  _relates_ = property(_get_relates, _set_relates)


def get(blog_id, post_id):
  """Returns post from memcache or datastore

  This method also updates if data is too old"""

  if post_id:
    key_name = 'b%dp%d' % (blog_id, post_id)
    p = memcache.get(key_name)
    if not p:
      p = Post.get_by_key_name(key_name)
      if not p:
        return None
      memcache.add(key_name, p, POST_CACHE_TIME)
    # Check if need to update
    if util.td_seconds(p.last_updated) > UPDATE_INTERVAL:
      labels = get_labels(blog_id, post_id)
      relates = []
      if labels:
        relates = get_relates(blog_id, post_id, labels)
      p = db.run_in_transaction(transaction_update_relates, blog_id, post_id, relates)
      memcache.set(key_name, p, POST_CACHE_TIME)
    return p
  return None


def add(blog_id, post_id):
  """Adds new post to db"""
  logging.debug('Adding %d, %d' % (blog_id, post_id))
  p = get(blog_id, post_id)
  if p:
    return p
  key_name = 'b%dp%d' % (blog_id, post_id)
  # Get labels of post
  labels = get_labels(blog_id, post_id)
  relates = []
  if isinstance(labels, list):
    relates = get_relates(blog_id, post_id, labels)
    p = db.run_in_transaction(transaction_add_post, blog_id, post_id, relates)
    memcache.set(key_name, p, POST_CACHE_TIME)
  return p


def get_labels(blog_id, post_id):
  logging.debug('Fetching labels for %d, %d' % (blog_id, post_id))
  f = urlfetch.fetch(POST_FETCH_URL % (blog_id, post_id))
  if f.status_code == 200:
    p_json = json.loads(f.content.replace('\t', '\\t'))
    entry = p_json['entry']
    labels = []
    if 'category' in entry:
      for cat in entry['category']:
        labels.append(cat['term'])
    return labels
  logging.debug('Unable to fetch labels: %d' % f.status_code)
  return f.status_code


def get_relates(blog_id, post_id, labels):
  logging.debug('Fetching relates for %d' % blog_id)
  # Nice Google: Disjunctions not supported yet
  # %7C = '|'
  # cat_query = urllib.quote('|'.join(labels))
  s_post_id = str(post_id)
  s_labels = sets.Set(labels)
  len_labels = len(labels)
  entries = []
  link_check = []
  for label in labels[:MAX_LABEL_QUERIES]:
    p_json = None
    json_content = memcache.get('b%dl%s' % (blog_id, label))
    if json_content:
      logging.debug('Got label %s from memcache' % label)
    else:
      logging.debug('Querying label %s' % label)
      f = urlfetch.fetch(POST_QUERY_URL % (blog_id, urllib.quote(label.encode('utf-8'))))
      if f.status_code == 200:
        json_content = f.content
        memcache.set('b%dl%s' % (blog_id, label), json_content, LABEL_QUERY_RESULT_CACHE_TIME)
        
    if json_content:
      try:
        p_json = json.loads(json_content)
      except ValueError:
        # TODO this is a temporary fix
        p_json = json.loads(json_content.replace('\t', '\\t'))

    if not p_json:
      logging.debug('Unable to retrieve for label %s: %d, %s' % (label, f.status_code, f.content))
      continue
      
    for entry in p_json['feed']['entry']:
      if entry['id']['$t'].find(s_post_id) >= 0:
        # Same post skip
        continue

      # Find the link to this related post
      link = ''
      for l in entry['link']:
        if l['rel'] == 'alternate':
          link = l['href']
          break
      # Skip if we already have this post
      if link in link_check:
        continue

      c_labels = []
      for cat in entry['category']:
        c_labels.append(cat['term'])

      match_count = len(s_labels & sets.Set(c_labels))
      if not match_count:
        # No label is matched
        continue

      entries.append((float(match_count) / len_labels, entry['title']['$t'], link))
      link_check.append(link)

  if entries:
    entries.sort()
    entries.reverse()
    entries = entries[:MAX_POSTS]
    # jsonize the result
    entries_json = {'entry': [dict(zip(('score', 'title', 'link'), entry)) for entry in entries]}
  else:
    entries_json = {'entry': []}
  return entries_json


def transaction_add_post(blog_id, post_id, relates):
  post = Post(key_name='b%dp%d' % (blog_id, post_id))
  post.blog_id = blog_id
  post.post_id = post_id
  post._relates_ = relates
  post.last_updated = util.now()
  post.put()
  return post


def transaction_update_relates(blog_id, post_id, relates):
  post = Post.get_by_key_name('b%dp%d' % (blog_id, post_id))
  post._relates_ = relates
  post.last_updated = util.now()
  post.put()
  return post

