#!/usr/bin/python
# Copyright 2011 Yu-Jie Lin
# New BSD License


from hashlib import md5
from tempfile import gettempdir

import ConfigParser
import datetime as dt
import optparse
import os
import shelve
import string
import sys
import textwrap

import gdata.analytics.client


__author__ = 'Yu-Jie Lin'
__copyright__ = "Copyright 2011, Yu-Jie Lin"
__credits__ = []
__license__ = "New BSD"
__version__ = '0.0.0.1'
__email__ = 'livibetter@gmail.com'
__status__ = 'Development'


SOURCE_APP_NAME = 'ga-stacked.py'


def retrieve_data(client, table_id, options):

  dimensions = []
  if options.dimensions:
    dimensions = options.dimensions.split(',')
  metrics = []
  if options.metrics:
    metrics = options.metrics.split(',')

  # Building query
  query = {
      'ids': table_id,
      'start-index': 1,
      'start-date': options.start_date,
      'end-date': options.end_date,
      'dimensions': ','.join(dimensions),
      'metrics': ','.join(metrics),
      'sort': options.sort,
      }
  if options.filters:
    query['filters'] = options.filters
  items_per_page = 1000
  query['max-results'] = min(items_per_page, options.limit) if options.limit else items_per_page

  # Retrieving data
  entries = []
  total_results = None
  print 'Retrieving data',
  while total_results is None or len(entries) < total_results:
    data_query = gdata.analytics.client.DataFeedQuery(query)
    feed = client.GetDataFeed(data_query)
    entries += feed.entry
    total_results = int(feed.total_results.text)
    if options.limit and options.limit < total_results:
      total_results = options.limit
    query['start-index'] = int(feed.start_index.text) + len(feed.entry)
    if options.limit and query['start-index'] + items_per_page > options.limit + 1:
      query['max-results'] = options.limit - query['start-index'] + 1
    sys.stdout.write('.')
    sys.stdout.flush()
  del query['start-index']
  del query['max-results']
  print ' %d entries retrieved.' % len(entries)
  print

  # Processing data
  data = []
  for entry in entries:
    data.append(
        [entry.dimension[i].value for i in range(len(entry.dimension))] +
        [float(m.value) for m in entry.metric])

  return {
      'results': data,
      'query': query,
      'dimensions': dimensions,
      'metrics': metrics,
      'metrics_start': len(dimensions),
      }


def group_data(data, options):

  dimensions = data['dimensions']
  # Which metric as value
  metric_index = data['metrics_start'] + options.m
  keys = []
  key_idxs = [int(g) for g in options.group.split(',')]
  dim_idxs = [idx for idx in range(len(dimensions)) if idx not in key_idxs]

  group_data = {}
  dim_values = set()
  for r in data['results']:
    key = ' '.join(r[idx] for idx in key_idxs)
    dim = ' '.join(r[idx] for idx in dim_idxs)
    metric_value = r[metric_index]
    dim_values.add(dim)
    if key not in group_data:
      keys.append(key)
      group_data[key] = {}
    group_data[key][dim] = metric_value
  # Fill keys do not have centain dimension values
  for key, dims in group_data.items():
    for dim_value in dim_values:
      if dim_value not in dims:
        dims[dim_value] = 0.0
    dims['all'] = sum(dims.values())
  data['group_data'] = group_data
  data['group_by'] = ','.join(dimensions[idx] for idx in key_idxs)
  data['key_idxs'] = key_idxs
  data['dim_idxs'] = dim_idxs
  data['keys'] = keys
  data['dim_values'] = dim_values


def sort_dims(dim_values, gdata):

  # Sort by dim's sum, highest value goes first
  sums = []
  for dim in dim_values:
    sums.append((sum(v[dim] for v in gdata.values()), dim))
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


def print_lr(left, right, width=80):

  print ('%s%%%ds' % (left, width - len(left))) % right


def print_text_result(data, options):

  if not data['results']:
    print 'Found no results'
    return

  gdata = data['group_data']
  dim_symbols = assign_symbols(sort_dims(data['dim_values'], gdata))

  keys = data['keys']
  dim_values = list(dim_symbols.keys())
  dim_values.sort()
  
  # plug into a ma filter
  new_data = {}
  if options.moving_average > 1:
    for idx in range(len(keys)):
      key = keys[idx]
      if key not in new_data:
        new_data[key] = {}
      for dim in dim_values:
        key_range = [i for i in range(idx - (options.moving_average - 1), idx + 1) if i >= 0]
        value = sum(gdata[keys[i]][dim] for i in key_range)
        value /= len(key_range)
        new_data[key][dim] = value
      new_data[key]['all'] = sum(new_data[key].values())
    gdata = new_data

  total_value = sum(v['all'] for v in gdata.values())
  max_all_value = max(v['all'] for v in gdata.values())

  query = data['query']
  width = options.width
  color = options.color
  center = options.center
  filled = options.filled
  print 'Dimensions: %s' % query['dimensions']
  print 'Group by  : %s' % data['group_by']
  print 'Metrics   : %s' % data['metrics'][options.m]
  print_lr('Filters   : %s' % query.get('filters', 'None'),
      'Date: %s -> %s' % (query['start-date'], query['end-date']), width)
  print_lr('Limit     : %d' % options.limit, max_all_value, width)
  print '-'*width

  key_width = max(len(k) for k in keys)
  line_width = width - key_width - 1
  for key in keys:
    if not max_all_value:
      # For some queries, API returns all zeros.
      print '%-*s' % (key_width, key)
      continue
    print '%-*s' % (key_width, key),
    dims = gdata[key]
    if not filled:
      line_width = int((width - key_width - 1.0) * dims['all'] / max_all_value)
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
      print '%s%s' % (' '*((width - key_width - 1 - line_width)/2), line)
    else:
      print line
  print '-'*width
  print_lr('Total: %s' % total_value, max_all_value, width)

  print_legend(dim_symbols, width=width, color=color)


def print_table(data, options):

  query = data['query']
  results = data['results']
  dimensions = data['dimensions']
  metrics = data['metrics']

  met_fmt = '%.3f'
  # Find field length
  dim_len = [0]*(len(dimensions))
  met_len = [0]*(len(metrics))
  met_sum = [0]*(len(metrics))

  for i in range(len(dim_len)):
    dim_len[i] = max(max(len(r[i]) for r in results), len(dimensions[i]))
  for i in range(len(met_len)):
    r_i = i + len(dim_len)
    met_sum[i] = sum(r[r_i] for r in results)
    met_len[i] = max(
        len(met_fmt % max(r[r_i] for r in results)),
        len(metrics[i]),
        len(met_fmt % met_sum[i]),
        )

  print 'Date  : %s -> %s' % (query['start-date'], query['end-date'])
  print 'Filter: %s' % query.get('filters', 'None')
  print 'Limit : %d' % options.limit
  print
  fmt_str = ' | '.join(filter(None, (
      ' '.join('%%-%ds' % dim_len[i] for i in range(len(dim_len))),
      ' '.join('%%%d.3f' % met_len[i] for i in range(len(met_len))),
      )))
  header = fmt_str.replace('.3f', 's') % tuple(data['dimensions'] + data['metrics'])
  print header
  print '-'*len(header)
  for r in results:
    print fmt_str % tuple(r)
  print '='*len(header)
  print fmt_str % tuple(['']*len(dim_len) + met_sum)

# BetterFormatter.py
# http://code.google.com/p/yjl/source/browse/Python/snippet/BetterFormatter.py
# Copyright (c) 2001-2006 Gregory P. Ward.  All rights reserved.
# Copyright (c) 2002-2006 Python Software Foundation.  All rights reserved.
# Copyright (c) 2011 Yu-Jie Lin.  All rights reserved.
# New BSD License

class BetterFormatter(optparse.IndentedHelpFormatter):

  def __init__(self, *args, **kwargs):

    optparse.IndentedHelpFormatter.__init__(self, *args, **kwargs)
    self.wrapper = textwrap.TextWrapper(width=self.width)

  def _formatter(self, text):

    return '\n'.join(['\n'.join(p) for p in map(self.wrapper.wrap,
        self.parser.expand_prog_name(text).split('\n'))])

  def format_description(self, description):

    if description:
      return self._formatter(description) + '\n'
    else:
      return ''

  def format_epilog(self, epilog):

    if epilog:
      return '\n' + self._formatter(epilog) + '\n'
    else:
      return ''

  def format_usage(self, usage):

    return self._formatter(optparse._("Usage: %s\n") % usage)

  def format_option(self, option):
    # Ripped and modified from Python 2.6's optparse's HelpFormatter
    result = []
    opts = self.option_strings[option]
    opt_width = self.help_position - self.current_indent - 2
    if len(opts) > opt_width:
      opts = "%*s%s\n" % (self.current_indent, "", opts)
      indent_first = self.help_position
    else:                       # start help on same line as opts
      opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
      indent_first = 0
    result.append(opts)
    if option.help:
      help_text = self.expand_default(option)
      # Added expand program name
      help_text = self.parser.expand_prog_name(help_text)
      # Modified the generation of help_line
      help_lines = []
      wrapper = textwrap.TextWrapper(width=self.help_width)
      for p in map(wrapper.wrap, help_text.split('\n')):
        if p:
          help_lines.extend(p)
        else:
          help_lines.append('')
      # End of modification
      result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
      result.extend(["%*s%s\n" % (self.help_position, "", line)
                     for line in help_lines[1:]])
    elif opts[-1] != "\n":
      result.append("\n")
    return "".join(result)


def main():

  usage = '%prog [options] EMAIL PASSWORD [TABLE_ID]'
  parser = optparse.OptionParser(formatter=BetterFormatter(), usage=usage, version='%%prog %s' % __version__,
      description='''If TABLE_ID isn't present, then %prog assumes that you want a list of profiles in your account, which contains TABLE IDs.''',
      epilog='''Notes: You may need to use --no-color if you are using Windows.''')

  parser.add_option('-d', '--dimensions',
      type='str', dest='dimensions', default='ga:date,ga:medium',
      help='Dimensions to chart with [default: %default]',
      )
  parser.add_option('-m', '--metrics',
      type='str', dest='metrics', default='ga:visits',
      help='Metrics data to download [default: %default]',
      )
  parser.add_option('-f', '--filters',
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
  parser.add_option('-g',
      type='str', dest='group', default='0',
      help='Which dimensions to group data, comma-separated-value of index values (0-based) of dimensions [default: %default]',
      )
  parser.add_option('--m',
      type='int', dest='m', default=0,
      help='Which metric for stacked area chart. 0-based index value [default: %default]',
      )
  parser.add_option('--sort',
      type='str', dest='sort', default='ga:date',
      help='Sory by which dimenstions',
      )
  parser.add_option('-l',
      type='int', dest='limit', default=0,
      help='Limit the number of returned result, 0 means no limit. [default: %default]',
      )
  parser.add_option('-a', '--moving-average',
      type='int', dest='moving_average', default=0,
      help='Length of moving average filter [default: %default]',
      )
  parser.add_option('-s', '--start-date',
      type='str', dest='start_date',
      default=(dt.datetime.utcnow() - dt.timedelta(days=30, hours=8)).strftime('%Y-%m-%d'),
      help='Date of the start of data [default: %default]',
      )
  parser.add_option('-e', '--end-date',
      type='str', dest='end_date',
      default=(dt.datetime.utcnow() - dt.timedelta(days=1, hours=8)).strftime('%Y-%m-%d'),
      help='Date of the end of data [default: %default]',
      )
  parser.add_option('--table',
      dest='print_table', default=False, action='store_true',
      help='Print a table of all dimensions and metrics',
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
  if options.start_date > options.end_date:
    parser.error('Date of the start must be earlier than or equal to date of the end')

  if len(args) == 3:
    account['table_id'] = args[2]
    print 'Read TABLE_ID from command-line'
  
  # Generate cache file name
  cache_file = os.sep.join([
      tmpdir,
      md5('|'.join([
          account['email'], account['table_id'],
          options.start_date, options.end_date,
          options.dimensions, options.metrics, options.filters,
          options.sort, str(options.limit),
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
    
    data = retrieve_data(client, account['table_id'], options)
    if options.use_cache:
      datafile = shelve.open(cache_file)
      datafile['data'] = data
      datafile.close()
      print 'Save data to cache file: %s' % cache_file
      print

  if options.print_table or not options.dimensions:
    print_table(data, options)
  else:
    group_data(data, options)
    print_text_result(data, options)


if __name__ == '__main__':
  main()
