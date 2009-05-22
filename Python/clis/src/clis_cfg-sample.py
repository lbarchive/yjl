# -*- coding: utf-8 -*-
#
# You can specify the sources you want to read in this file. All sources must
# be placed inside of
#   sources = [
#       SOURCE1
#       SOURCE2
#       ...
#       ]
# Each source should look like
#   {
#       'setting_name': 'setting_value',
#        ...
#   },
#
# For output* templating syntax please read
#   http://www.simple-is-better.org/template/pyratemp.html
# For date_fmt date format please read
#   http://docs.python.org/library/datetime.html?highlight=strftime#strftime-behavior
#
# All commented out setting are also the defualt values, if you need to
# customize, then remove the prefixing '#' character.

sources = [
   {
        # Twitter: Statuses of you and whom you follow
        'type': 'twitter',
        #src_name': 'Twitter',
        'username': 'username', 
        'password': 'secret', 
        #interval': 90, 
        #'output': '@!ansi.fgreen!@@!status.created_at!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!status.user.screen_name!@@!ansi.freset!@: @!status.text!@ @!ansi.fmagenta!@http://twitter.com/@!status.user.screen_name!@/status/@!status.id!@@!ansi.freset!@',
        #'date_fmt': '%H:%M:%S',
        },
   {
        # FriendFeed Home Realtime - Only activiies after run, no session data will be stored
        # Item structure can be found at http://code.google.com/p/friendfeed-api/wiki/ApiDocumentation#Reading_FriendFeed_Feeds
        'type': 'friendfeed',
        #src_name': 'FriendFeed',
        'nickname': 'nickname',
        'remote_key': 'secret',
        #'interval': 60,
        # Available object: entry, ansi, src_name
        #'output': '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["user"]["nickname"]!@@!ansi.freset!@:<!--(if "room" in entry)--> @!ansi.fiyellow!@[@!entry["room"]["name"]!@]@!ansi.freset!@<!--(end)--> @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@http://friendfeed.com/e/@!entry["id"]!@@!ansi.freset!@',
        # Available object: entry, like, ansi, src_name
        #'output_like': '@!ansi.fgreen!@@!like["date"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!like["user"]["nickname"]!@@!ansi.freset!@ @!ansi.fired!@♥@!ansi.freset!@ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@http://friendfeed.com/e/@!entry["id"]!@@!ansi.freset!@',
        # Available object: entry, comment, ansi, src_name
        #'output_comment': '@!ansi.fgreen!@@!comment["date"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!comment["user"]["nickname"]!@@!ansi.freset!@ ✎ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@: @!comment["body"]!@ @!ansi.fmagenta!@http://friendfeed.com/e/@!entry["id"]!@@!ansi.freset!@',
        #'show_like': True,
        #'show_comment': True,
        #'date_fmt': '%H:%M:%S',
        },
   {
        # Feed: Normal feed
        'type': 'feed',
        #src_name': 'Feed',
        'feed': 'http://example.com/feed',
        #'interval': 60,
        'output': '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!entry.link!@@!ansi.freset!@',
        #'date_fmt': '%H:%M:%S',
        },
   {
        # GMail: Mails in inbox
        'type': 'gmail',
        #'src_name': 'Gmail',
        'email': 'email@gmail.com',
        'password': 'secret',
        #'interval': 60,
        #'output': '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ @!ansi.fred!@[@!src_name!@]@!ansi.freset!@ @!ansi.fyellow!@@!entry["author"]!@@!ansi.freset!@: @!ansi.bold!@@!entry["title"]!@@!ansi.reset!@ @!entry["link"]!@',
        #'date_fmt': '%H:%M:%S',
        },
   {
        # Google Reader: Items of subscriptions
        'type': 'greader',
        #'src_name': 'GReader',
        'email': 'email@gmail.com',
        'password': 'secret',
        #'interval': 60,
        #'output': '@!ansi.fgreen!@@!entry["updated"]!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["source"]["title"]!@@!ansi.freset!@@!ansi.freset!@: @!ansi.bold!@@!entry["title"]!@@!ansi.reset!@ @!entry["link"]!@',
        #'date_fmt': '%H:%M:%S',
        },
   ]
