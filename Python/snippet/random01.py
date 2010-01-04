#!/usr/bin/env python


import random
import sys


r = random.Random()
b = ['0', '1']

sys.stdout.write('\033[32;40m')
for i in range(int(sys.argv[2])):
  for i in range(int(sys.argv[1])):
    sys.stdout.write(r.choice(b))
  sys.stdout.write('\n')

sys.stdout.write('\033[0m')
