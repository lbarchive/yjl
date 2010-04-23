#!/usr/bin/env python
# text2image.py
#
# Examples:
#  ./text2image.py test.txt test.png
#  ./text2image.py test.txt test.gif
#  ./text2image.py - manual_input.png
#  ls -l | ./text2image.py - dirs.png


from optparse import OptionParser

import Image
import ImageDraw
import ImageFont
import sys


__author__ = 'Yu-Jie Lin'
__copyright__ = "Copyright 2010, Yu-Jie Lin"
__credits__ = []
__license__ = "New BSD"
__version__ = '0.0.0.1'
__email__ = 'livibetter@gmail.com'
__status__ = 'Development'


def main():

  usage = 'usage: %prog [options] (in_text|-) out_image'
  parser = OptionParser(usage=usage, version='%%prog %s' % __version__)
  parser.add_option('-f', '--font',
      type='str', dest='font',
      help='Font file for rendering text',
      )
  parser.add_option('-s', '--size',
      type='int', dest='size', default=12,
      help='Font size (only available for TrueType of OpenType fonts) [default: %default]',
      )
  parser.add_option('-p', '--padding',
      type='int', dest='padding', default=5,
      help='Text to border in pixels [default: %default]',
      )
  parser.add_option('-l', '--line-height',
      type='float', dest='line_height', default=1.1,
      help='Line height in font-height [default: %default]',
      )
  parser.add_option('-b', '--background',
      type='str', dest='background', default='#444',
      help='Background color [default: %default]',
      )
  parser.add_option('-c', '--color',
      type='str', dest='color', default='#aaa',
      help='Text color [default: %default]',
      )
  parser.add_option('--border',
      type='int', dest='border', default=5,
      help='Border width in pixels [default: %default]',
      )
  parser.add_option('--border-color',
      type='str', dest='border_color', default='#000',
      help='Border color [default: %default]',
      )
  options, args = parser.parse_args()

  if len(args) != 2:
    parser.error('Need both in_text (or -, from standard input) and out_image')

  # Loading font
  if options.font:
    try:
      if options.font.endswith('.ttf') or options.font.endswith('.otf'):
        font = ImageFont.truetype(options.font, options.size)
      else:
        font = ImageFont.load(options.font)
    except IOError, e:
      print e
      parser.error('Can not load font from %s' % options.font)
  else:
    font = ImageFont.load_default()

  in_text, out_image  = args

  # Preparing the text
  if in_text == '-':
    if sys.stdin.isatty():
      if sys.platform == 'win32':
        print '( Press Control+Z, then Return at new line to finish )'
      else:
        print '( Press Control+D, then Return at new line to finish )'
    text = sys.stdin.readlines()
  else:
    if not sys.stdin.isatty():
      parser.error('in_text should be -, if you intend to pipe in your text.')
    f = open(in_text)
    text = f.read().split('\n')
    f.close()

  # Find the nessecary width and font height
  font_height = 0
  width = 0
  for t in text:
    w, h = font.getsize(t)
    if w > width:
      width = w
    if h > font_height:
      font_height = h

  # Calculating image size
  width += options.padding * 2 + options.border * 2
  height = int(options.line_height * font_height * len(text)) + \
      options.padding * 2 + options.border * 2

  # Creating new image to draw text
  image = Image.new('RGB', (width, height), options.background)
  draw = ImageDraw.Draw(image)

  # Drawing border
  if options.border:
    draw.rectangle((0, 0, width, options.border - 1),
        fill=options.border_color)
    draw.rectangle((0, height - options.border, width, height - 1),
        fill=options.border_color)
    draw.rectangle((0, 0, options.border - 1, height - 1),
        fill=options.border_color)
    draw.rectangle((width - options.border, 0, width, height - 1),
        fill=options.border_color)

  starting_offset = options.padding + options.border

  for i in range(len(text)):
    draw.text((starting_offset, starting_offset + 
        int(i * options.line_height * font_height)),
        text[i], font=font, fill=options.color)

  image.save(out_image)


if __name__ == '__main__':
  main()
