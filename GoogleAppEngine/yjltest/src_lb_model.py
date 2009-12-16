from google.appengine.ext import db


class SearchResultCount(db.Model):

  date = db.DateProperty(required=True)
  google = db.IntegerProperty()
  yahoo = db.IntegerProperty()
  bing = db.IntegerProperty()
