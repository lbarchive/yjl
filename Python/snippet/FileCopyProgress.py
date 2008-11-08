#!/usr/bin/python
# Code snippet: Copying a file with progress reporting
#
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
#
# Author : Yu-Jie Lin
# Website: http://friendfeed.com/livibetter


import os
import random
import shutil
import sys
import threading
import time


# You can create a 128MB test.bin using
# head -c 128m /dev/urandom > test.bin
INPUT_FILENAME = 'test.bin'
CHUCK_SIZE = 1024 * 1024


# functions for testing
def GetTempFilename():
  a = '0123456789ABCDEF'
  count = 10
  while True:
    f = 'TEST-'
    for i in range(8):
      f += a[random.randint(0, len(a) - 1)]
    f += '.tmp'
    if not os.path.exists(f):
      break
    count -= 1
    if count < 0:
      raise "Can not find a temporary filename."
  return f


def PrintProgress(filename, current, total):
  percent = 100.0 * current / total
  # CR carrier return
  sys.stdout.write('\x0D')
  sys.stdout.write('%s [' % filename)
  i_per = int(percent) / 2
  ii_per = 100 / 2 - i_per
  sys.stdout.write('#'*i_per)
  sys.stdout.write(' '*ii_per)
  sys.stdout.write('] [%7.2f %%]' % percent)
  sys.stdout.flush()


def CopyChuck():
  out_filename = GetTempFilename()
  filesize = os.stat(INPUT_FILENAME).st_size
  print "Copying chuck by chuck..."
  try:
    fin = open(INPUT_FILENAME, 'rb')
    fout = open(out_filename, 'wb')
    try:
      while fout.tell() < filesize - 1:
        fout.write(fin.read(CHUCK_SIZE))
        fout.flush()
        PrintProgress(out_filename, fout.tell(), filesize)
    finally:
      fin.close()
      fout.close()
  except IOError:
    print 'Can not open input or output files.'
  print


def CopyInThread():
  def copyfile(src, desc):
    try:
      # See also shutil.copyfileobj()
      shutil.copyfile(src, desc)
    except IOError:
      print 'Unable to copy file'
      return False
    return True

  out_filename = GetTempFilename()
  filesize = os.stat(INPUT_FILENAME).st_size
  print "Copying in thread..."
  copy_thread = threading.Thread(target=copyfile,
      args=(INPUT_FILENAME, out_filename))
  copy_thread.start()
  current = 0
  while current < filesize:
    try:
      current = os.stat(out_filename).st_size
      PrintProgress(out_filename, current, filesize)
    except OSError:
      pass
    time.sleep(0.1)
  print


# main plate of spaghetti

CopyChuck()
CopyInThread()
