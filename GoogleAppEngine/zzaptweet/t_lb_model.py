from google.appengine.ext import db


class TwitterLbRecord(db.Model):

  date = db.DateTimeProperty(required=True)
  friends = db.IntegerProperty()
  followers = db.IntegerProperty()
  tweets = db.IntegerProperty()
  tweets_per_day = db.FloatProperty()
  favourites = db.IntegerProperty()
