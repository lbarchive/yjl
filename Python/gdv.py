#!/usr/bin/env python
# Google Docs Viewer helper for local documents
# Copyright 2011 Yu-Jie Lin
# New BSD License


from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from contextlib import closing
from optparse import OptionParser
from os.path import abspath, basename
from urllib import quote

import mimetypes
import socket
import sys
import time
import urllib2
import webbrowser


__author__ = 'Yu-Jie Lin'
__copyright__ = "Copyright 2011, Yu-Jie Lin"
__credits__ = []
__license__ = "New BSD"
__version__ = '0.0.0.1'
__email__ = 'livibetter@gmail.com'
__status__ = 'Development'


class RequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    
    if basename(self.path) != quote(basename(self.server.doc_file)):
      self.send_error(403)
    else:
      self.send_response(200);
      if self.server.doc_file_type[0]:
        self.send_header('Content-Type', self.server.doc_file_type[0])
      else:
        self.send_header('Content-Type', 'application/octet-stream')
      self.end_headers()
      with open(self.server.doc_file) as f:
        self.wfile.write(f.read())
    self.server.sent = True

  def log_message(self, *args):

    pass


def get_my_IP():

  with closing(urllib2.urlopen('http://icanhazip.com/')) as f:
    data = f.read().strip('\n')
  return data


def main():

  print 'gdv.py %s' % __version__
  print

  usage = 'usage: %prog [options] document_file'
  parser = OptionParser(usage=usage, version='%%prog %s' % __version__)
  parser.add_option('-p', '--port',
      type='int', dest='port', default=8000,
      help='Port number of HTTP Server [default: %default]',
      )
  options, args = parser.parse_args()

  if len(args) != 1:
    parser.error('Need document file and only support one file')

  # Get file path and type
  doc_file = args[0]
  doc_file = abspath(doc_file)
  doc_file_type = mimetypes.guess_type(doc_file)
  print 'File: %s' % doc_file
  print 'Type: %s' % doc_file_type[0]
  print

  # Get external IP address
  IP = get_my_IP()

  print 'Starting HTTP Server %s:%d...' % (IP, options.port),
  httpd = HTTPServer((IP, options.port), RequestHandler)
  httpd.doc_file = doc_file
  httpd.doc_file_type = doc_file_type
  httpd.sent = False
  print 'started.'
  print

  # Checking port
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    s.connect((IP, options.port))
    s.shutdown(1)
  except:
    print '%s:%d does not seem to be accessible.' % (IP, options.port)
    print 'You may need to open the port. If you uses iptables, you can run:'
    print '  $ iptables -I INPUT 1 -p tcp --dport %d -j ACCEPT' % options.port
    print
    print 'After the file is sent, you can close the port:'
    print '  $ iptables -D INPUT -p tcp --dport %d -j ACCEPT' % options.port
    sys.exit(2)
    return
  
  doc_URL = 'http://%s:%d/%s' % (IP, options.port, quote(basename(doc_file)))
  gdv_URL = 'http://docs.google.com/viewer?url=%s' % quote(doc_URL)
  print 'Opening in web browser...'
  webbrowser.open(gdv_URL, new=2, autoraise=True)
  print 'If browser does not show up, please navigate manually at'
  print '  %s' % gdv_URL
  print
  
  print 'Waiting for a request in...',
  sys.stdout.flush()
  while not httpd.sent:
    httpd.handle_request()
    time.sleep(0.1)
  print 'file sent.'

if __name__ == '__main__':
  main()
