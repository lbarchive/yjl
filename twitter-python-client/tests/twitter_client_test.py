#!/usr/bin/python
#
# Copyright (C) 2008 Yu-Jie Lin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unittest for Twitter Client"""


__author__ = 'livibetter (Yu-Jie Lin)'


import datetime
import unittest

import twitter_client as tc
from twitter_client import test_data


class ItemsPerPageTest(unittest.TestCase):

  def setUp(self):
    self.items_per_page = tc.ItemsPerPage()

  def testGet(self):
    self.items_per_page.text = 'text'
    self.assertRaises(ValueError, self.items_per_page.Get)

  def testSet(self):
    self.assertRaises(ValueError, self.items_per_page.Set, 'text')

  def testToAndFromString(self):
    self.items_per_page.Set(15)
    self.assert_(self.items_per_page.Get() == 15)
    new_items_per_page = tc.ItemsPerPageFromString(self.items_per_page.ToString())
    self.assert_(self.items_per_page.Get() == new_items_per_page.Get())


class LanguageTest(unittest.TestCase):

  def setUp(self):
    self.language = tc.Language()

  def testToAndFromString(self):
    self.language.Set('en')
    self.assert_(self.language.Get() == 'en')
    new_language = tc.LanguageFromString(self.language.ToString())
    self.assert_(self.language.Get() == new_language.Get())


class WarningTest(unittest.TestCase):

  def setUp(self):
    self.warning = tc.Warning()

  def testToAndFromString(self):
    self.warning.Set('warning')
    self.assert_(self.warning.Get() == 'warning')
    new_warning = tc.WarningFromString(self.warning.ToString())
    self.assert_(self.warning.Get() == new_warning.Get())


class DateTest(unittest.TestCase):

  def setUp(self):
    self.date = tc.Date()

  def testToAndFromString(self):
    now = datetime.datetime.utcnow().replace(microsecond=0)
    self.date.Set(now)
    self.assert_(self.date.Get() == now)
    new_date = tc.DateFromString(self.date.ToString())
    self.assert_(self.date.Get() == new_date.Get())


class PublishedTest(unittest.TestCase):

  def setUp(self):
    self.published = tc.Published()

  def testToAndFromString(self):
    now = datetime.datetime.utcnow().replace(microsecond=0)
    self.published.Set(now)
    self.assert_(self.published.Get() == now)
    new_published = tc.PublishedFromString(self.published.ToString())
    self.assert_(self.published.Get() == new_published.Get())


class UpdatedTest(unittest.TestCase):

  def setUp(self):
    self.updated = tc.Updated()

  def testToAndFromString(self):
    now = datetime.datetime.utcnow().replace(microsecond=0)
    self.updated.Set(now)
    self.assert_(self.updated.Get() == now)
    new_updated = tc.UpdatedFromString(self.updated.ToString())
    self.assert_(self.updated.Get() == new_updated.Get())


class SearchResultEntryTest(unittest.TestCase):

  def testToAndFromString(self):
    published=datetime.datetime(2008, 10, 10, 1, 2, 3)
    updated=datetime.datetime(2009, 11, 12, 2, 3, 4)

    entry = tc.SearchResultEntry(
        published=tc.Published(),
        updated=tc.Updated(),
        )
    entry.published.Set(published)
    entry.updated.Set(updated)
    self.assert_(entry.published.Get() == published)
    self.assert_(entry.updated.Get() == updated)

    new_entry = tc.SearchResultEntryFromString(entry.ToString())
    self.assert_(new_entry.published.Get() == published)
    self.assert_(new_entry.updated.Get() == updated)
    
  def testConvertActualData(self):
    feed = tc.SearchResultFeedFromString(test_data.SEARCH_RESULT_FEED)
    self.assert_(len(feed.entry) == 1)
    entry = feed.entry[0]
    self.assert_(entry.GetMessageID() == '955300766')
    self.assert_(isinstance(entry, tc.SearchResultEntry))
    self.assert_(isinstance(entry.published, tc.Published))
    self.assert_(isinstance(entry.updated, tc.Updated))
    self.assert_(entry.published.Get() == datetime.datetime(2008, 10, 11, 9, 34, 37))
    self.assert_(entry.updated.Get() == datetime.datetime(2008, 10, 11, 9, 34, 37))


class SearchResultFeedTest(unittest.TestCase):

  def testToAndFromString(self):
    feed = tc.SearchResultFeed(
       warning=tc.Warning().Set('warning'),
       items_per_page=tc.ItemsPerPage().Set(15),
       language=tc.Language().Set('en'),
       )
    self.assert_(feed.warning.Get() == 'warning')
    self.assert_(feed.items_per_page.Get() == 15)
    self.assert_(feed.language.Get() == 'en')

    new_feed = tc.SearchResultFeedFromString(feed.ToString())
    self.assert_(feed.warning.Get() == new_feed.warning.Get())
    self.assert_(feed.items_per_page.Get() == new_feed.items_per_page.Get())
    self.assert_(feed.language.Get() == new_feed.language.Get())

  def testConvertActualData(self):
    feed = tc.SearchResultFeedFromString(test_data.SEARCH_RESULT_FEED)
    self.assert_(
        feed.warning.Get() == 'adjusted since_id, it was older than allowed')
    self.assert_(feed.items_per_page.Get() == 15)
    self.assert_(feed.language.Get() == 'en')


if __name__ == '__main__':
  unittest.main()
