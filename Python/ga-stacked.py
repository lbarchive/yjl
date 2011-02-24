#!/usr/bin/python
# Copyright 2011 Yu-Jie Lin
# New BSD License


from hashlib import md5
from optparse import OptionParser
from tempfile import gettempdir

import ConfigParser
import datetime as dt
import os
import shelve
import string
import sys

import gdata.analytics.client


__author__ = 'Yu-Jie Lin'
__copyright__ = "Copyright 2011, Yu-Jie Lin"
__credits__ = []
__license__ = "New BSD"
__version__ = '0.0.0.1'
__email__ = 'livibetter@gmail.com'
__status__ = 'Development'


SOURCE_APP_NAME = 'ga-stacked.py'


group_funcs = {
    'week_sun': lambda date: date.strftime('%Yw%U'),
    'week_mon': lambda date: date.strftime('%Yw%W'),
    'month': lambda date: date.strftime('%Y-%m'),
    'year': lambda date: date.strftime('%Y'),
    }


def retrieve_data(client, table_id, dates, dimension='ga:medium', metric='ga:visits', filters=''):

  data = {}
  query = {
      'ids': table_id,
      'start-date': dates[0],
      'end-date': dates[1],
      'dimensions': ('ga:date,' + dimension).rstrip(','),
      'sort': 'ga:date',
      'metrics': metric,
      }
  if filters:
    query['filters'] = filters
  items_per_page = 1000
  query['max-results'] = items_per_page

  entries = []
  total_results = None
  print 'Retrieving data',
  while total_results is None or len(entries) < total_results:
    data_query = gdata.analytics.client.DataFeedQuery(query)
    feed = client.GetDataFeed(data_query)
    entries += feed.entry
    total_results = int(feed.total_results.text)
    query['start-index'] = int(feed.start_index.text) + len(feed.entry)
    sys.stdout.write('.')
    sys.stdout.flush()
  del query['start-index']
  del query['max-results']
  print ' %d entries retrieved.' % len(entries)
  print

  dim_values = set()
  for entry in entries:
    e_date = entry.dimension[0].value
    e_dim = ' '.join(dim.value for dim in entry.dimension[1:])
    dim_values.add(e_dim)
    date = dt.date(int(e_date[0:4]), int(e_date[4:6]), int(e_date[6:8]))
    if date not in data:
      data[date] = {}
    data[date][e_dim] = float(entry.metric[0].value)
  # Fill dates do not have centain dimension values
  for date, dims in data.items():
    for dim_value in dim_values:
      if dim_value not in dims:
        dims[dim_value] = 0.0
    dims['all'] = sum(dims.values())
  # Store metadata, this might be useful for later use
  dim_values = list(dim_values)
  dim_values.sort()
  data['meta'] = {
      'query': query,
      'total_results': total_results,
      'dim_values': dim_values,
      }
  return data


def sort_dims(dim_values, data):

  # Sort by dim's sum, highest value goes first
  sums = []
  for dim in dim_values:
    sums.append((sum(v[dim] for v in data.values()), dim))
  sums.sort()
  sums.reverse()
  return [dim for s, dim in sums]


def assign_symbols(dim_values):

  accepted_sym = (string.ascii_letters + string.digits + string.punctuation).replace('?', '')
  
  symbols = {}
  not_assigned = []
  for dim in dim_values:
    for c in dim:
      if c not in symbols and c in accepted_sym:
        symbols[c] = dim
        accepted_sym = accepted_sym.replace(c, '')
        break
    else:
      # All char in dim are already in use
      not_assigned.append(dim)

  # Swap key and value
  symbols = dict((v, k) for k, v in symbols.items())

  # Give those unassigned a common symbol
  for dim in not_assigned:
    if accepted_sym:
      c, accepted_sym = accepted_sym[0], accepted_sym[1:]
    else:
      c = '?'
    symbols[dim] = c

  # Assign color code
  for idx in range(len(dim_values)):
    dim = dim_values[idx]
    color = '%d' % (31 + idx % 12 % 6)
    if idx % 12 % 2 == 1:
      color += ';1'
    symbols[dim] = {
        'color': color,
        'symbol': symbols[dim],
        }

  return symbols


def print_legend(dim_symbols, width=80, color=True):
 
  keys = [(v['symbol'], k) for k, v in dim_symbols.items()]
  keys.sort(lambda a, b: ord(a[0][0]) - ord(b[0][0]))
  
  if len(keys) == 1 and not keys[0][1]:
    # This chart should be the result without querying dimensions
    return
  
  indent = 2
  left_space = 0
  print 'Legend:',
  for idx in range(len(keys)):
    dim = keys[idx][1]
    symbol = dim_symbols[dim]['symbol']
    use_space = len(dim) + 4 # 2 spaces, ',', and symbol
    if color and symbol in dim:
      use_space -= 2 # only ',', and symbol

    if use_space > left_space:
      print
      sys.stdout.write(' '*indent)
      left_space = width - indent
    if color:
      sym_color = dim_symbols[dim]['color']
      if symbol in dim:
        print dim.replace(symbol, '\033[%sm%s\033[0m' % (sym_color, symbol), 1),
      else:
        print '\033[%sm%s\033[0m %s' % (sym_color, symbol, dim),
    else:
      print '%s %s' % (symbol, dim),
    if idx < len(keys) - 1:
      sys.stdout.write(', ')
    left_space -= use_space
  print


def print_text_result(data, width=80, filled=False, moving_average=0, grouping=None, center=False, color=True):

  if not data['meta']['total_results']:
    print 'Found no results'
    return

  # Don't mess with original data
  data = data.copy() 
  # Make sure meta isn't in data
  meta = data.pop('meta')
  dim_symbols = assign_symbols(sort_dims(meta['dim_values'], data))

  dates = list(data.keys())
  dates.sort()
  dim_values = list(dim_symbols.keys())
  dim_values.sort()
  
  # grouping
  new_data = {}
  new_dates = []
  if grouping:
    for idx in range(len(dates)):
      date = dates[idx]
      new_date = group_funcs[grouping](date)
      if new_date not in new_data:
        new_data[new_date] = dict(zip(dim_values, [0.0]*len(dim_values)))
        new_dates.append(new_date)
      for dim in dim_values:
        new_data[new_date][dim] += data[date][dim]
    for new_date in new_data.keys():
      new_data[new_date]['all'] = sum(new_data[new_date].values())
    data = new_data
    dates = new_dates

  # plug into a ma filter
  new_data = {}
  if moving_average > 1:
    for idx in range(len(dates)):
      date = dates[idx]
      if date not in new_data:
        new_data[date] = {}
      for dim in dim_values:
        date_range = [i for i in range(idx - 2, idx + 1) if i >= 0]
        value = sum(data[dates[i]][dim] for i in date_range)
        value /= len(date_range)
        new_data[date][dim] = value
      new_data[date]['all'] = sum(new_data[date].values())
    data = new_data

  max_all_value = max(v['all'] for v in data.values())

  query = meta['query']
  dim = query['dimensions'].replace('ga:date', '').lstrip(',')
  if not dim:
    dim = 'None'
  date = 'Date: %s -> %s' % (query['start-date'], query['end-date'])
  print ('Dimensions: %s%%%ds' % (dim, width - len(dim) - len('Dimensions: '))) % date
  print 'Metric    : %s' % query['metrics']
  print ('Filter    : %s%%%df' % (query.get('filters', 'None'),
      width - len(query.get('filters', 'None')) - len('Filter    : '))) % max_all_value
  print '-'*width

  date_width = len(dates[0])
  line_width = width - date_width - 1
  for idx in range(len(dates)):
    date = dates[idx]
    if not max_all_value:
      # For some queries, API returns all zeros.
      print date
      continue
    print date,
    dims = data[date]
    if not filled:
      line_width = int((width - date_width - 1.0) * dims['all'] / max_all_value)
    acc_pos = 0.0
    line = ''
    area_width = 0
    for m_idx in range(len(dim_values)):
      dim = dim_values[m_idx]
      value = dims[dim]
      if not value:
        continue
      symbol = dim_symbols[dim]['symbol']
      w1 = int(round((acc_pos + value) / dims['all'] * line_width))
      w2 = int(round(acc_pos / dims['all'] * line_width))
      dim_width = w1 - w2
      acc_pos += value
      if not dim_width:
        continue
      if color: 
        sym_color = dim_symbols[dim]['color']
        line += '\033[%sm%s\033[0m' % (sym_color, symbol*dim_width)
      else:
        line += symbol*dim_width
      area_width += dim_width
    if center:
      print '%s%s' % (' '*((width - date_width - 1 - line_width)/2), line)
    else:
      print line
  print '-'*width
  print ('%%%df' % width) % max_all_value
  print_legend(dim_symbols, width=width, color=color)


def main():

  usage = 'usage: %prog [options] EMAIL PASSWORD [TABLE_ID]'
  parser = OptionParser(usage=usage, version='%%prog %s' % __version__,
      description='''If TABLE_ID isn't present, then %prog assumes that you want a list of profiles in your account, which contains TABLE IDs.''',
      epilog='''You may need to use --no-color if you are using Windows.''')

  parser.add_option('-d', '--dimension',
      type='str', dest='dimension', default='ga:medium',
      help='Dimension to chart with [default: %default]',
      )
  parser.add_option('-m', '--metric',
      type='str', dest='metric', default='ga:visits',
      help='Metric to chart with [default: %default]',
      )
  parser.add_option('-f', '--filter',
      type='str', dest='filters', default='',
      help='Filter for querying data',
      )
  parser.add_option('-w', '--width',
      type='int', dest='width', default=80,
      help='Width of chart [default: %default]',
      )
  parser.add_option('-c', '--center',
      dest='center', default=False, action='store_true',
      help='Align to center of lines [default is not center-aligned]',
      )
  parser.add_option('-A', '--no-color',
      dest='color', default=True, action='store_false',
      help='Do not use ANSI escape code for colors [colors in use by default]',
      )
  parser.add_option('-C', '--no-cache',
      dest='use_cache', default=True, action='store_false',
      help='Do not read or write to a cache file [cache in use by default]',
      )
  parser.add_option('-F', '--no-fill',
      dest='filled', default=True, action='store_false',
      help='Do not fill the chart [chart is filled by default]',
      )
  parser.add_option('-i', '--config',
      type='str', dest='config',
      help='Configuration file for general account settings',
      )
  parser.add_option('-t', '--section',
      type='str', dest='section',
      help='Section of configuration file',
      )
  parser.add_option('-g', '--group-by',
      type='str', dest='group',
      help='Groupping data [values: %s]' % ', '.join(group_funcs.keys()),
      )
  parser.add_option('-a', '--moving-average',
      type='int', dest='moving_average', default=0,
      help='Length of moving average filter [default: %default]',
      )
  parser.add_option('-s', '--date-start',
      type='str', dest='date_start',
      default=(dt.datetime.utcnow() - dt.timedelta(days=30, hours=8)).strftime('%Y-%m-%d'),
      help='Date of the start of data [default: %default]',
      )
  parser.add_option('-e', '--date-end',
      type='str', dest='date_end',
      default=(dt.datetime.utcnow() - dt.timedelta(days=1, hours=8)).strftime('%Y-%m-%d'),
      help='Date of the end of data [default: %default]',
      )

  options, args = parser.parse_args()

  # Prepare cache dir
  tmpdir = os.sep.join([gettempdir(), SOURCE_APP_NAME])
  if not os.path.exists(tmpdir):
    os.makedirs(tmpdir, 0700)

  account = {'email': None, 'password': None, 'table_id': None}

  # Load config file
  if options.config:
    config = ConfigParser.ConfigParser()
    config.read(options.config)
    print 'Loading config %s:' % options.config,
    sections = ['general']
    if options.section:
      sections.append(options.section)
    for section in sections:
      if config.has_section(section):
        for option in ['email', 'password', 'table_id']:
          if config.has_option(section, option):
            option_value = config.get(section, option)
            account[option] = option_value
            print '[%s] %s,' % (section, option),
      elif section != 'general':
        parser.error('Cannot find section %s' % option.section)
    print 'Done.'
  
  if len(args) >= 2:
    account['email'] = args[0]
    account['password'] = args[1]
    print 'Read EMAIL, PASSWORD from command-line'
  if account['email'] and account['password'] and not account['table_id']:
    # List table ids
    client = gdata.analytics.client.AnalyticsClient(source=SOURCE_APP_NAME)
    client.ClientLogin(account['email'], account['password'],
        source=SOURCE_APP_NAME)
    account_query = gdata.analytics.client.AccountFeedQuery()
    feed = client.GetAccountFeed(account_query)
    fmt = '%%-%ds %%-%ds' % (options.width/2, options.width - options.width/2)
    print fmt % ('Web Property ID', 'Table ID')
    print fmt % ('Account Name', 'Profile Name')
    print '='*options.width
    for entry in feed.entry:
      print fmt % (entry.GetProperty('ga:webPropertyId').value,
          entry.table_id.text)
      print fmt % (entry.GetProperty('ga:accountName').value,
          entry.title.text)
      print '-'*options.width
    return
  
  if not (account['email'] and account['password'] and account['table_id']):
    parser.error('Need EMAIL PASSWORD TABLE_ID')
  if options.date_start > options.date_end:
    parser.error('Date of the start must be earlier than or equal to date of the end')
  if options.group and options.group not in group_funcs.keys():
    parser.error('Data can only be groupped by one of %s' % ', '.join(group_funcs.keys()))

  if len(args) == 3:
    account['table_id'] = args[2]
    print 'Read TABLE_ID from command-line'
  
  # Generate cache file name
  cache_file = os.sep.join([
      tmpdir,
      md5('|'.join([
          account['email'], account['table_id'],
          options.date_start, options.date_end,
          options.dimension, options.metric, options.filters,
          ])).hexdigest()
      ])

  # Try to load data from cache file
  data = None
  if options.use_cache and os.path.exists(cache_file):
    datafile = shelve.open(cache_file)
    data = datafile.get('data', None)
    datafile.close()
    print 'Found cache file: %s' % cache_file
    print

  # If no data, then retrieve data via API
  if data is None:
    client = gdata.analytics.client.AnalyticsClient(source=SOURCE_APP_NAME)
    client.ClientLogin(account['email'], account['password'],
        source=SOURCE_APP_NAME)
    
    data = retrieve_data(client, account['table_id'],
        [options.date_start, options.date_end],
        options.dimension, options.metric, options.filters,
        )
    if options.use_cache:
      datafile = shelve.open(cache_file)
      datafile['data'] = data
      datafile.close()
      print 'Save data to cache file: %s' % cache_file
      print

  print_text_result(data, width=options.width, filled=options.filled,
      grouping=options.group, moving_average=options.moving_average,
      center=options.center, color=options.color
      )


if __name__ == '__main__':
  main()
