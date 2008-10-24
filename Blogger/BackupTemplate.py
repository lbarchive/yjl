#!/usr/bin/python
#
# BackupTemplate - Backup templates of blogs on Blogger.com
#
# Copyright (C) 2008 Yu-Jie Lin
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
# 
#
# Author       : Yu-Jie Lin
# Website      : http://code.google.com/p/yjl/wiki/BackupTemplate
# Creation Date: 2008-10-24T06:58:06+0800


__author__ = 'livibetter@gmail.com (Yu-Jie Lin)'


import datetime
import getpass
import re

from gdata.blogger.service import BloggerService
import gdata.blogger


email = raw_input('Please enter your email: ')
password = getpass.getpass()

# TODO: Remove this temporary fix when gdata.py gets updated
gdata.blogger.BlogEntry.blog_id_pattern = \
    re.compile('tag:blogger.com,1999:user-(\d+)\.blog-(\d+)')

date_tag = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

client = BloggerService(email=email, password=password,
    source="YJL-BackupTemplate-0")
client.ProgrammaticLogin()

feed = client.GetBlogFeed()

for blog in feed.entry:
  blog_id = blog.GetBlogId()
  blog_name = blog.GetBlogName()

  print 'Retrieving template of %s...' % blog_name,
  for link in blog.link:
    if link.rel == 'http://schemas.google.com/blogger/2008#template':
      break
  else:
    print
    print 'ERROR: Can not find a link to download template of %s!' % blog_name
    continue

  template = client.Get(uri=link.href).entry[0].content.text
  try:
    file = open('%s-%s-%s.xml' % (blog_id, blog_name, date_tag), 'w')
    try:
      file.write(template)
    finally:
      file.close()
  except:
    print
    print 'ERROR: Can not open file to write!'
  print 'done'

