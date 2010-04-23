#!/usr/bin/env python


import sys


def main():

  args = sys.argv[1:]
  
  print 'Usage: %s [-|filename] or using pipe.\n' % sys.argv[0]
  
  if sys.stdin.isatty():
    if len(args) == 1 and args[0] != '-':
      print '=== from file ==='
      text = ['* %s *' % args[0]]
    else:
      if sys.platform == 'win32':
        print '( Press Control+Z, then Return at new line to finish )'
      else:
        print '( Press Control+D, then Return at new line to finish )'
      text = sys.stdin.readlines()
      print '=== from manual input ==='
  else:
    if len(args) == 1 and args[0] != '-':
      print >> sys.stderr, 'Argument should be -, if you intend to pipe in your text.'
      sys.exit(1)
    text = sys.stdin.readlines()
    print '=== from pipe ==='
  
  print ''.join(text)


if __name__ == '__main__':
  main()
