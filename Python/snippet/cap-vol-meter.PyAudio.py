#!/usr/bin/env python
# Written by Yu-Jie Lin
# Modified code from the following link for using PyAudio:
#   http://blog.yjl.im/2011/02/capture-device-volume-meter.html
# BSD License

import math
import optparse
import os
import struct
import sys
import time

import pyaudio

def color(value, ch, color):

  if not color:
    return ch
  if value > 80:
    return '\033[31;1m%s\033[0m' % ch
  if value > 40:
    return '\033[33;1m%s\033[0m' % ch
  return '\033[32;1m%s\033[0m' % ch


if __name__ == '__main__':

  parser = optparse.OptionParser()
  parser.add_option('--card',
      type='str', dest='card', default='default',
      help='Capture device on which card [default: %default]',
      )
  parser.add_option('-c', '--channels',
      type='int', dest='channels', default=2,
      help='How many channels to monitor [default: %default]',
      )
  parser.add_option('-w', '--width',
      type='int', dest='width', default=int(os.environ.get('COLUMNS', 80)),
      help='Width of chart [default: %default]',
      )
  parser.add_option('--ch',
      # If use unicode in default, optparse bitches
      type='str', dest='ch', default=None,
      help=u'Character for a meter unit. Be sure this will be a single '
          'character [default: %s]' % unichr(9726),
      )
  parser.add_option('-C', '--no-color',
      dest='color', default=True, action='store_false',
      help='Use for boring life [colors in use by default]',
      )

  options, args = parser.parse_args()
  if options.ch is None:
    options.ch = unichr(9726).encode('utf-8')
 
  p = pyaudio.PyAudio()
  pcm_in = p.open(
    format=pyaudio.paInt16,
    channels=options.channels,
    rate=8000,
    input=True,
    frames_per_buffer=1024)

  SLEEP = 0.04
  WIDTH = options.width - 10
  peak = [0]*options.channels
  peak_time = [0]*options.channels
  PEAK_TIME = 10
  DEC_PEAK_TIME = 1
  PEAK_RANGE = 5
  BLOCK_SIZE = 64
  C_LEN = len(color(0, options.ch, options.color))
  COLOR_BAR = ''.join(color(100 * pos / WIDTH, options.ch, options.color) for pos in range(WIDTH))
  print '\033[2J\033[H'
  try:
    while True:
      l = max(pcm_in.get_read_available() / BLOCK_SIZE, 1) * BLOCK_SIZE
      data = pcm_in.read(l)
      udata = struct.unpack('%dh' % (l * options.channels), data)
      MAX = math.log(32768**2*l)
      sys.stdout.write('\033[H')
      for idx in range(options.channels):
        value = sum(map(lambda v: v**2, udata[idx::options.channels]))
        value = 100 * math.log(max(value, 1)) / MAX
        # rescale
        value = 100 * (max(value - 50, 0) / 50)
        pos = int(WIDTH * value / 100)
        if pos - peak[idx] > PEAK_RANGE:
          peak[idx] = pos
          peak_time[idx] = PEAK_TIME
        elif pos > peak[idx]:
          peak_time[idx] = 0
        sys.stdout.write('\033[0J\033[37;1mCH %d\033[0m %s %s' % (
            idx, color(value, '%3d%%' % value, options.color), COLOR_BAR[:C_LEN*pos]))
        if peak_time[idx] > 0:
          sys.stdout.write('\033[%dG' % (peak[idx] + 10))
          sys.stdout.write(COLOR_BAR[C_LEN*peak[idx]-C_LEN:C_LEN*peak[idx]])
          peak_time[idx] -= 1
        elif peak[idx] > pos:
          peak[idx] -= 1
          # Reducing flickering
          sys.stdout.write('\033[%dG' % (peak[idx] + 10))
          sys.stdout.write(COLOR_BAR[C_LEN*peak[idx]-C_LEN:C_LEN*peak[idx]])
          peak_time[idx] = DEC_PEAK_TIME
        sys.stdout.write('\n')
      time.sleep(SLEEP)
  except KeyboardInterrupt:
    print 'Bye.'

  pcm_in.stop_stream()
  pcm_in.close()
  p.terminate()
