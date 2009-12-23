# Copyright (c) 2009, Yu-Jie Lin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the organization nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY Yu-Jie Lin ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Yu-Jie Lin BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Live Demo
# =========
#
# http://yjltest.appspot.com/i18n
#
# Internationlization of Django
# =============================
#
# Here we assume that you don't run entire Django framework. In the entry
# script, we need to configure correctly in order to get Django's i18n worked.
# Please read the imports in this script.
#
# Then we will need to specify what string needs to be translated, please
# refer to http://www.djangoproject.com/documentation/0.96/i18n/
#
# Next step is to generate message files. In order to get the Django's utility
# worked, we will need to create few directories:
#
#   $ mkdir -p /path/to/myapp/conf/locale
#
# Run make-messages.py
#
#   $ cd /path/to/myapp
#   $ PYTHONPATH=/path/to/googleappengine/lib/django/ /path/to/googleappengine/lib/django/django/bin/make-messages.py -l en
#
# Where /path/to/googleappengine is the location of Google App Engine SDK.
# Now we should have /path/to/conf/locale/en/LC_MESSAGES/django.po. Create
# languages as many as we need and translate them. If the code gets modified,
# run make-messages.py -a to update all message files.
#
# You also need to specify the CHARSET of message file, at least. Usually
# UTF-8 will be fine, the line would read like:
#
#   "Content-Type: text/plain; charset=UTF-8\n"
#
# Once finishing the translation, run the following to compile
#
#   $ PYTHONPATH=/path/to/googleappengine/lib/django/ /path/to/googleappengine/lib/django/django/bin/compile-messages.py
#
# Django's i18n can decide language per user. Normally it will be done by
# using LocaleMiddleware. Since we don't run entire Django framework, we need
# to deal it on our own, that is the util.I18NRequestHandler (read util.py in
# this project directory).


import logging
import os

from google.appengine.ext import webapp
# template import must be run before other Django modules imports
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

# Set the Django setting file, we must create it in
# /path/to/myapp/
#   | conf/
#   +   __init__.py
#   +   settings.py
#   +   locale/
#
# Because django.util.translation will read locale/ from where setting.py
# locates, therefore we need to put it into conf/.
os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None

# I18NRequestHandler handles what django.middleware.locale.LocaleMiddleware
# does for setting in Cookie/Header. It wraps the
# google.appenine.ext.webapp.RequestHandler
from util import I18NRequestHandler


class I18NPage(I18NRequestHandler):

  def get(self):

    cookie_django_language = self.request.get('cookie_django_language', '')
    if cookie_django_language:
      if cookie_django_language == 'unset':
        del self.request.COOKIES['django_language']
      else:
        self.request.COOKIES['django_language'] = cookie_django_language
      self.reset_language()

    template_values = {
      'title': _('Internationalization'),
      }

    path = os.path.join(os.path.dirname(__file__), 'template/i18n.html')
    self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication([
    ('/i18n', I18NPage),
    ],
    debug=True)
    

def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
