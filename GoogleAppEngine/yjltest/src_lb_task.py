from datetime import datetime
import re

from google.appengine.api.urlfetch import fetch

from src_lb_model import SearchResultCount

BING_APPID = 'F102804AE27C06275E0B535689E4134DABC92FBA'
RE_GOOGLE = re.compile('"estimatedResultCount":"([0-9]+)"')
RE_BING = re.compile('"Total":([0-9]+)')


class UnableToSearch(Exception):

  pass


def src_lb_update():

  today = datetime.utcnow().date()
  record = SearchResultCount.all().filter('date =', today).get()
  if record:
    # Already has today's data
    return

  keyword = 'livibetter'
  
  f = fetch('http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s' % keyword)
  if f.status_code != 200:
    raise UnableToSearch('Failed to search on Google')
  m = RE_GOOGLE.search(f.content)
  if not m:
    raise UnableToSearch('Failed to find result on Google Results')
  google = int(m.group(1))
  
 
  f = fetch('http://api.bing.net/json.aspx?AppId=%s&Version=2.2&Market=en-US&Query=%s&Sources=web&Web.Count=1' % (BING_APPID, keyword))
  if f.status_code != 200:
    raise UnableToSearch('Failed to search on Bing')
  m = RE_BING.search(f.content)
  if not m:
    import logging
    logging.debug(f.content)
    raise UnableToSearch('Failed to find result on Bing Results')
  bing = int(m.group(1))
  
  record = SearchResultCount(date=today, google=google, bing=bing)
  record.put()
