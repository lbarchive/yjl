#!/usr/bin/env python
# Copyright 2010 Yu-Jie Lin
# BSD license

import email
import email.header
import imaplib
import sys

# http://google-mail-xoauth-tools.googlecode.com/svn/trunk/python/xoauth.py
import xoauth

scope = 'https://mail.google.com/'
consumer = xoauth.OAuthEntity('anonymous', 'anonymous')
imap_hostname = 'imap.googlemail.com'

# How many messages will be fetched for listing?
MAX_FETCH = 20


try:
  import config
except ImportError:
  class Config():
    pass
  config = Config()


def get_access_token():
 
  request_token = xoauth.GenerateRequestToken(
      consumer, scope, nonce=None, timestamp=None,
      google_accounts_url_generator=config.google_accounts_url_generator
      )

  oauth_verifier = raw_input('Enter verification code: ').strip()
  try:
    access_token = xoauth.GetAccessToken(
        consumer, request_token, oauth_verifier, config.google_accounts_url_generator)
  except ValueError:
    # Could indicate failure of authentication because verifier is incorrect
    print 'Incorrect verification code?'
    sys.exit(1)
  return access_token


def main():
  
  # Checking user email and access token
  if not hasattr(config, 'user') or not hasattr(config, 'access_token'):
    config.user = raw_input('Please enter your email address: ')
    config.google_accounts_url_generator = xoauth.GoogleAccountsUrlGenerator(config.user)
    access_token = get_access_token()
    config.access_token = {'key': access_token.key, 'secret': access_token.secret}
    # XXX save token, this is not a good way, I'm too lazy to use something
    # like shelve.
    f = open('config.py', 'w')
    f.write('user = %s\n' % repr(config.user))
    f.write('access_token = %s\n' % repr(config.access_token))
    f.close()
    print '\n\nconfig.py written.\n\n'

  config.google_accounts_url_generator = xoauth.GoogleAccountsUrlGenerator(config.user)
  access_token = xoauth.OAuthEntity(config.access_token['key'], config.access_token['secret'])

  # Generate xoauth string
  class ImBad():
    # I'm bad because I'm going to shut xoauth's mouth up. So you won't see these debug messages:
    # signature base string:
    # GET&https%3A%2F%2Fmail.google.com%2Fmail%2Fb%2Flivibetter%40gmail.com%...
    #
    # xoauth string (before base64-encoding):
    # GET https://mail.google.com/mail/b/livibetter@gmail.com/IMAP/ oauth_co...
    def write(self, msg): pass
  sys.stdout = ImBad()
  xoauth_string = xoauth.GenerateXOauthString(
      consumer, access_token, config.user, 'IMAP',
      xoauth_requestor_id=None, nonce=None, timestamp=None)
  sys.stdout = sys.__stdout__

  MINSIZE = int(raw_input('Larger than in KB [1000]? ') or 1000)
  MAXSIZE = int(raw_input('Smaller than in KB [5000]? ') or 5000)
  if MAXSIZE < MINSIZE:
    print >> sys.stderr, 'Wrong size range!'
    sys.exit(1)
  print
  imap_conn = imaplib.IMAP4_SSL(imap_hostname)
  imap_conn.authenticate('XOAUTH', lambda x: xoauth_string)
  imap_conn.select('[Gmail]/All Mail', readonly=True)
  typ, data = imap_conn.search(None, '(SMALLER %d) (LARGER %d)' % (MAXSIZE * 1000, MINSIZE * 1000))
  # No SORT command on Gmail IMAP server
  #typ, data = imap_conn.sort('(REVERSE SIZE)', 'UTF-8', '(LARGER %d)' % SIZE)
  unreads = data[0].split()
  print '%d messages are between %d and %d KB.' % (len(unreads), MINSIZE, MAXSIZE)
  ids = ','.join(unreads[:MAX_FETCH])
  if ids:
    print
    print 'Listing %d messages:' % min(len(unreads), MAX_FETCH)
    typ, data = imap_conn.fetch(ids, '(RFC822.HEADER)')
    for item in data:
      if isinstance(item, tuple):
        raw_msg = item[1]
        msg = email.message_from_string(raw_msg)
        # Some email's header are encoded, for example: '=?UTF-8?B?...'
        print '\033[1;35m%s\033[0m: \033[1;32m%s\033[0m' % (
            email.header.decode_header(msg['from'])[0][0],
            email.header.decode_header(msg['subject'])[0][0],
            )
  imap_conn.close()
  imap_conn.logout()


if __name__ == '__main__':
  main()
