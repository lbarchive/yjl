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

"""Contains extensions to Atom objects used with Twitter API."""


__author__ = 'livibetter (Yu-Jie Lin)'


import atom


# XML namespaces which are often used in Twitter API entities.
OPENSEARCH_NAMESPACE = 'http://a9.com/-/spec/opensearch/1.1/'
OPENSEARCH_TEMPLATE = '{http://a9.com/-/spec/opensearch/1.1/}%s'
TWITTER_NAMESPACE = 'http://api.twitter.com/'
TWITTER_TEMPLATE = '{http://api.twitter.com/}%s'


# Base Model

class Base(atom.AtomBase):

  def Get(self):
    """Gets self.text in more proper type"""
    return self.text

  def Set(self, text):
    """Sets self.text via more proper type"""
    self.text = text
    return self


# OpenSearch Data Models

class ItemsPerPage(Base):
  _tag = 'itemsPerPage'
  _namespace = OPENSEARCH_NAMESPACE

  def Get(self):
    return int(self.text)

  def Set(self, items):
    """Sets Items Per Page

    Args:
      items: int The number of items per page
    """
    self.text = str(int(items))
    return self


def ItemsPerPageFromString(xml_string):
  return atom.CreateClassFromXMLString(ItemsPerPage, xml_string)


class Language(Base):
  _tag = 'language'
  _namespace = OPENSEARCH_NAMESPACE


def LanguageFromString(xml_string):
  return atom.CreateClassFromXMLString(Language, xml_string)


# Twitter API Data Models

class Warning(Base):
  _tag = 'warning'
  _namespace = TWITTER_NAMESPACE


def WarningFromString(xml_string):
  return atom.CreateClassFromXMLString(Warning, xml_string)


class LinkFinder(atom.LinkFinder):

  def GetLinkByRel(self, rel):
    for link in self.link:
      if rel == link.rel:
        return link
    return None


# Search API
class SearchResultEntry(atom.Entry, LinkFinder):
  """A Twitter Search Result Entry flavor of Atom Entry"""

  def __GetId(self):
    return self.__id

  def __SetId(self, id):
    self.__id = id
    if id is not None and id.text is not None:
      self.__id.text = id.text.strip()

  id = property(__GetId, __SetId)


def SearchResultEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(SearchResultEntry, xml_string)


class SearchResultFeed(atom.Feed, LinkFinder):
  """A Twitter Search Result Feed flavor of Atom Feed"""

  _tag = atom.Feed._tag
  _namespace = atom.Feed._namespace
  _children = atom.Feed._children.copy()
  _attributes = atom.Feed._attributes.copy()
  _children['{%s}warning' % TWITTER_NAMESPACE] = (
      'warning', Warning)
  _children['{%s}itemsPerPage' % OPENSEARCH_NAMESPACE] = (
      'items_per_page', ItemsPerPage)
  _children['{%s}language' % OPENSEARCH_NAMESPACE] = (
      'language', Language)
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [SearchResultEntry])
  del _children['{%s}category' % atom.ATOM_NAMESPACE]
  del _children['{%s}generator' % atom.ATOM_NAMESPACE]
  del _children['{%s}author' % atom.ATOM_NAMESPACE]
  del _children['{%s}contributor' % atom.ATOM_NAMESPACE]
  del _children['{%s}logo' % atom.ATOM_NAMESPACE]
  del _children['{%s}icon' % atom.ATOM_NAMESPACE]
  del _children['{%s}rights' % atom.ATOM_NAMESPACE]
  del _children['{%s}subtitle' % atom.ATOM_NAMESPACE]

  def __GetId(self):
    return self.__id

  def __SetId(self, id):
    self.__id = id
    if id is not None and id.text is not None:
      self.__id.text = id.text.strip()

  id = property(__GetId, __SetId)

  def __init__(self, atom_id=None, title=None, entry=None,
      link=None, warning=None, updated=None,
      items_per_page=None, language=None,
      extension_elements=None, extension_attributes=None, text=None):
    """Constructor for Source
    
    Args:
      id: Id (optional) The entry's Id element
      link: list (optional) A list of Link instances
      title: Title (optional) The entry's Title element
      updated: Updated (optional) The entry's Updated element
      entry: list (optional) A list of the Entry instances contained in the 
          feed.
      warning: Warning (optional) The entry's Warning element.
      items_per_page: ItemsPerPage (optional) The entry's ItemsPerPage element of
                      OpenSearch.
      language: Language (optional) The entry's Language element of OpenSearch.
      text: String (optional) The text contents of the element. This is the 
          contents of the Entry's XML text node. 
          (Example: <foo>This is the text</foo>)
      extension_elements: list (optional) A list of ExtensionElement instances
          which are children of this element.
      extension_attributes: dict (optional) A dictionary of strings which are 
          the values for additional XML attributes of this element.
    """

    self.id = atom_id
    self.link = link or []
    self.title = title
    self.updated = updated
    self.entry = entry or []
    self.warning = warning
    self.items_per_page = items_per_page
    self.language = language
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def SearchResultFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SearchResultFeed, xml_string)


