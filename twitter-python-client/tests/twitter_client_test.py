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


class SearchResultEntryTest(unittest.TestCase):

  def testConvertActualData(self):
    feed = tc.SearchResultFeedFromString(test_data.SEARCH_RESULT_FEED)
    self.assert_(len(feed.entry) == 1)
    entry = feed.entry[0]
    self.assert_(isinstance(entry, tc.SearchResultEntry))


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
