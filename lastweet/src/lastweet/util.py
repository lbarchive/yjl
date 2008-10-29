import datetime


def td_seconds(t):
  """Returns timedelta of now to t in seconds"""
  td = (datetime.datetime.utcnow() - t)
  return td.days * 86400 + td.seconds + td.microseconds / 1000000.0


def now(utc=True):
  """Returns UTC time if utc, otherwise local time"""
  if utc:
    return datetime.datetime.utcnow()
  return datetime.datetime.now()
