#!/usr/bin/env python
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


class TrackerThread(threading.Thread, IdleTracker):

  def __init__(self, idle_threshold=300000, callback_idle=None,
      callback_unidle=None):

    threading.Thread.__init__(self)
    IdleTracker.__init__(self, idle_threshold=idle_threshold)

    self.callback_idle = callback_idle
    self.callback_unidle = callback_unidle

  def run(self):
    
    while True:
      info = self.check_idle()
      if info[0] == 'idle' and self.callback_idle:
        self.callback_idle()
      elif info[0] == 'unidle' and self.callback_unidle:
        self.callback_unidle()
      time.sleep(max(info[1] / 1000, 5))    


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
  tracker_thread = TrackerThread(away_time * 1000, do_idle, do_unidle)
  tracker_thread.setDaemon(True)
  tracker_thread.start()

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
