__copyright__ = """
Copyright (c) 2001-2006 Gregory P. Ward.  All rights reserved.
Copyright (c) 2002-2006 Python Software Foundation.  All rights reserved.
Copyright (c) 2011 Yu-Jie Lin.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

  * Neither the name of the author nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import optparse
import textwrap

class BetterFormatter(optparse.IndentedHelpFormatter):

  def __init__(self, *args, **kwargs):

    optparse.IndentedHelpFormatter.__init__(self, *args, **kwargs)
    self.wrapper = textwrap.TextWrapper(width=self.width)

  def _formatter(self, text):

    return '\n'.join(['\n'.join(p) for p in map(self.wrapper.wrap,
        self.parser.expand_prog_name(text).split('\n'))])

  def format_description(self, description):

    if description:
      return self._formatter(description) + '\n'
    else:
      return ''

  def format_epilog(self, epilog):

    if epilog:
      return '\n' + self._formatter(epilog) + '\n'
    else:
      return ''

  def format_usage(self, usage):

    return self._formatter(optparse._("Usage: %s\n") % usage)

  def format_option(self, option):
    # Ripped and modified from Python 2.6's optparse's HelpFormatter
    result = []
    opts = self.option_strings[option]
    opt_width = self.help_position - self.current_indent - 2
    if len(opts) > opt_width:
      opts = "%*s%s\n" % (self.current_indent, "", opts)
      indent_first = self.help_position
    else:                       # start help on same line as opts
      opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
      indent_first = 0
    result.append(opts)
    if option.help:
      help_text = self.expand_default(option)
      # Added expand program name
      help_text = self.parser.expand_prog_name(help_text)
      # Modified the generation of help_line
      help_lines = []
      wrapper = textwrap.TextWrapper(width=self.help_width)
      for p in map(wrapper.wrap, help_text.split('\n')):
        if p:
          help_lines.extend(p)
        else:
          help_lines.append('')
      # End of modification
      result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
      result.extend(["%*s%s\n" % (self.help_position, "", line)
                     for line in help_lines[1:]])
    elif opts[-1] != "\n":
      result.append("\n")
    return "".join(result)
