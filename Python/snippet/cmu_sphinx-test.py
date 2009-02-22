#!/usr/bin/python
#
# This file is in the Public Domain
# Should be ok with
#  CMU sphinxbase 0.4.1
#  CMU pocketsphinx 0.5.1
#  pyalsaaudio 0.4
#
# Author: Yu-Jie Lin
# http://sites.google.com/site/livibetter/


import os
from tempfile import mkstemp
import time

import alsaaudio as alsa

import pocketsphinx as ps


if __name__ == '__main__':

  # Make a temporary file
  fd, filename = mkstemp()
  # Open the file
  buf = os.fdopen(fd, 'w+b')
  #d = ps.Decoder(hmm='/usr/share/pocketsphinx/model/hmm/wsj1', lm='/usr/share/pocketsphinx/model/lm/wsj/wlist5o.3e-7.vp.tg.lm.DMP', dict='/usr/share/pocketsphinx/model/lm/wsj/wlist5o.dic')
  d = ps.Decoder(hmm='/usr/share/pocketsphinx/model/hmm/wsj1', lm='/usr/share/pocketsphinx/model/lm/turtle/turtle.lm.DMP', dict='/usr/share/pocketsphinx/model/lm/turtle/turtle.dic')

  # Prepare the CAPTURE device. It must use 16k Hz, litten endian, 16 bit signed integer
  pcm_in = alsa.PCM(alsa.PCM_CAPTURE, alsa.PCM_NONBLOCK, 'default')
  pcm_in.setchannels(1)
  pcm_in.setrate(16000)
  pcm_in.setformat(alsa.PCM_FORMAT_S16_LE)
  # Size of block of each read
  pcm_in.setperiodsize(512)

  print  
  print 'Recording and recognizing on the fly...', 'Press Ctrl+C to stop'
  try:
    # Start to recognize
    d.start_utt()
    while True:
      # Read data from device
      l, data = pcm_in.read()

      if l:
        # Send to pocketsphinx
        d.process_raw(data, False, False)
        # Write to buffer for decoding by block
        buf.write(data)

      time.sleep(.001)
  except KeyboardInterrupt:
    # Stop the CAPTURE device
    pcm_in.pause()
    # End of decoding
    d.ps_end_utt()
    buf.close()
  # Get the result of on-the-fly
  r_on_the_fly = d.get_hyp()
  # Get the file handle of temporary file
  buf = open(filename, 'rb')
  d.decode_raw(buf)
  buf.close()
  r_block = d.get_hyp()

  print
  print 'Result on decoding on the fly:', r_on_the_fly
  print 'Result on decoding on a block:', r_block
  os.remove(filename)
