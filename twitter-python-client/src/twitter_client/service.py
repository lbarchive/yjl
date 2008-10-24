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

"""TwitterService streamlines Twitter operations.

  TwitterService: Provides methods to query feeds and manipulate items.
"""

__author__ = 'livibetter (Yu-Jie Lin)'

import urllib
import atom.service
import atom
import twitter_client as tc


class TwitterService(atom.service.AtomService):
  """Client for the Twitter service."""

  def Search(self, query, converter=tc.SearchResultFeedFromString):
    """Searchs on Twitter via Search API

    Args:
      query: str Querying string.
    """
    response = self.Get('http://search.twitter.com/search.atom?q=' +
        urllib.quote_plus(query))
    response = response.read()
    if converter:
      return converter(response)
    return response

