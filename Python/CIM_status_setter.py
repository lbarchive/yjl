#!/usr/bin/env python
# Copytright 2009 Yu-Jie Lin ( http://livibetter.mp/ )
#
# This script is licensed under the GPLv3
#
# This script requires one of the follows:
#   PyXSS  : http://bebop.bigasterisk.com/python
#     Install this by standard way
#   pxss.py: http://code.google.com/p/yjl/source/browse/Python/pxss.py
#     Put pxss.py with this script

try:
  from pxss import IdleTracker
except ImportError:
  from xss import IdleTracker

import os
import select
import sys
import termios
import time
import threading
import tty
import traceback


# BEGIN SETTINGS =======

# Away time in seconds
away_time = 300
# Specify protocols you need: icq, yahoo, msn, aim, irc, jab, rss, lj, gg or
# infocard
protocols = ['msn', 'jab']
# Set detect at startup?
detect_startup = True

# END OF SETTING =======

MODE_KEYS = ['o', '_', 'a', 'd', 'n', 'c', 'f', 'i']
MODE_DESC = {'o': 'Online', '_': 'Offline', 'a': 'Away',
    'd': 'Do not disturb', 'n': 'Not available', 'c': 'Occupied',
    'f': 'Free for chat', 'i': 'Invisible'}
QUIT_KEYS = ['x', 'q']

# Current status
status = '?'
# Detecting?
detect = False


def p(msg, newline=True):

  sys.stdout.write(msg)
  if newline:
    sys.stdout.write('\r\n')
  sys.stdout.flush()


def do_idle():
 
  if not detect:
    return

  set_status('a')
  print_status()
  p('   Hello!?', False)


def do_unidle():

  if not detect:
    return

  set_status('o')
  print_status()
  p('   Welcome back!', False)


def getch():

  global p_stdin
  
  if p_stdin.poll(1000):
    return sys.stdin.read(1)
  else:
    return None


def show_help():

  p('')
  p('Keys')
  p(' h - Show help')
  p(' * - Detect idling')
  p(' %s - Change status' % ', '.join(MODE_KEYS))
  print_status()


def set_status(new_status):

  global status

  for p in protocols:
    os.system('centerim -p %s -S %s' % (p, new_status))
  status = new_status


def print_status():

  # Clean up
  p('\033[2K\r', False)

  d = '*' if detect else ' '
  p('[%s][%s] %s' % (d, status, MODE_DESC[status]), False)

  # Set up window title
  if 'TERM' in os.environ:
    if os.environ['TERM'] == 'screen':
      os.system('screen -X title "%s"' % MODE_DESC[status])
    else:
      p('\033]0;%s\007' % MODE_DESC[status], False)


def main():

  global detect, p_stdin

  tty.setraw(sys.stdin.fileno())

  p_stdin = select.poll()
  # Register for data-in
  p_stdin.register(sys.stdin, select.POLLIN)
  
  set_status('o')
  if detect_startup:
    detect = True
  show_help()
  
  # Initialize the tracker
  tracker = IdleTracker(idle_threshold=away_time * 1000)

  t_mark = time.time()

  # Looping
  while True:
    ch = getch()
    if ch:
      ch = ch.lower()
      if ch == 'h':
        show_help()
      elif ch == '*':
        detect = True
        # User presses the key, must be online
        set_status('o')
        print_status()
      elif ch in MODE_KEYS:
        detect = False
        set_status(ch)
        print_status()
      elif ch in QUIT_KEYS:
        break
    else:
      if time.time() > t_mark:
        info = tracker.check_idle()
        if info[0] == 'idle':
          do_idle()
        elif info[0] == 'unidle':
          do_unidle()
        t_mark = time.time() + max(info[1] / 1000.0, 5)

  p('')
  p('Bye!')


if __name__ == "__main__":
  p('\033[?25l', False)
  # Get stdin file descriptor
  fd = sys.stdin.fileno()
  old_settings = termios.tcgetattr(fd)
  try:
    main()
  except:
    termios.tcsetattr(fd, termios.TCSANOW, old_settings)
    p('\033[?25h', False)
    p('')
    traceback.print_exc()
  finally:
    termios.tcsetattr(fd, termios.TCSANOW, old_settings)
    p('\033[?25h', False)
