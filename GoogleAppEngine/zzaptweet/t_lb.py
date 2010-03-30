import os

from google.appengine.api import memcache
from google.appengine.api.labs.taskqueue import TaskAlreadyExistsError
from google.appengine.ext import db, deferred, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from t_lb_model import TwitterLbRecord
from t_lb_task import t_lb_update


class HomePage(webapp.RequestHandler):

  def get(self):

    results = TwitterLbRecord.all().order('-date').fetch(1000)
    tmpl_values = {
        'results': results,
        }
    path = os.path.join(os.path.dirname(__file__), 'template/t_lb.html')
    self.response.out.write(template.render(path, tmpl_values))

  def head(self):

    pass


class CronPage(webapp.RequestHandler):

  def get(self):

    try:
      deferred.defer(t_lb_update)
      self.response.out.write('Task added')
    except TaskAlreadyExistsError:
      self.response.out.write('Task existed')


application = webapp.WSGIApplication([
    ('/', HomePage),
    ('/t_lb_cron', CronPage),
    ],
    debug=True)


def main():
  
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
