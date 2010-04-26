# -*- coding: utf-8 -*-
#
# Due to services' license agreement or terms of service, you also must agree
# with; or
#  * Do not run clis
#  * Do not use service that the limitation which you can not comply
#  * Replace with your own key. A key is an identification data that service
#    can identify an application.
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
#
# Available functions:
#   * http://www.simple-is-better.org/template/pyratemp.html#expressions
#   * ftime(date, format)
#       For format of strftime method, please read
#         http://docs.python.org/library/time.html#time.strftime
#   * surl(url) - Shorten url
#
# All commented settings are the defualt values, if you need to customize, then
# remove the prefixing '#' character.

sources = [
    {
        # Twitter: Statuses of you and whom you follow
        'type': 'twitter',
        #src_name': 'Twitter',
        'username': 'username',
        # Get your keys here: http://dev.twitter.com/apps/new
        'consumer_key': 'YOUR_KEY', # Double Check :)
        'consumer_secret': 'YOUR_SECRET', # Double Check :)
        #interval': 90,
        # status.tweet_link - URL of Tweet
        #'output': '@!ansi.fgreen!@@!ftime(status["created_at"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!status["user"]["screen_name"]!@@!ansi.freset!@: @!unescape(status["text"])!@ @!ansi.fmagenta!@@!surl(status["tweet_link"])!@@!ansi.freset!@'
        },
    {
        'type': 'twittersearch',
        #'src_name': 'TwitterSearch',
        # You can make one easier at http://search.twitter.com/advanced
        'q': 'the search term',
        # How many returned result in one query, upto 100
        #'rpp': 15,
        # A valid ISO 639-1 code (http://en.wikipedia.org/wiki/ISO_639-1)
        #'lang': 'en',
        #'interval': 60,
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
        # entry["_link"] - URL of entry
        #'output': '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["user"]["nickname"]!@@!ansi.freset!@:<!--(if "room" in entry)--> @!ansi.fiyellow!@[@!entry["room"]["name"]!@]@!ansi.freset!@<!--(end)--> @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@@!surl(entry["_link"])!@@!ansi.freset!@',
        # Available object: entry, like, ansi, src_name
        #'output_like': '@!ansi.fgreen!@@!ftime(like["date"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!like["user"]["nickname"]!@@!ansi.freset!@ @!ansi.fired!@♥@!ansi.freset!@ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@ @!ansi.fmagenta!@@!surl(entry["_link"])!@@!ansi.freset!@',
        # Available object: entry, comment, ansi, src_name
        #'output_comment': '@!ansi.fgreen!@@!ftime(comment["date"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!comment["user"]["nickname"]!@@!ansi.freset!@ ✎ @!ansi.fcyan!@@!entry["title"]!@@!ansi.freset!@: @!comment["body"]!@ @!ansi.fmagenta!@@!surl(entry["_link"])!@@!ansi.freset!@',
        #'show_like': True,
        #'show_comment': True,
        # You may have set hidding some people's item, you can decide if you
        # still want to see them.
        #'show_hidden': False,
        },
    {
        # Feed: Normal feed
        'type': 'feed',
        #src_name': 'Feed',
        'feed': 'http://example.com/feed',
        #'interval': 60,
        #'output': '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry.link)!@@!ansi.freset!@',
        },
    {
        # GMail: Mails in inbox
        'type': 'gmail',
        #'src_name': 'Gmail',
        'email': 'email@gmail.com',
        'password': 'secret',
        #'interval': 60,
        #'output': '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ @!ansi.fred!@[@!src_name!@]@!ansi.freset!@ @!ansi.fyellow!@@!entry["author"]!@@!ansi.freset!@: @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry["link"])!@@!ansi.freset!@',
        },
    {
        # Google Reader: Items of subscriptions
        'type': 'greader',
        #'src_name': 'GReader',
        'email': 'email@gmail.com',
        'password': 'secret',
        #'interval': 60,
        #'output': '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!ansi.fyellow!@@!entry["source"]["title"]!@@!ansi.freset!@: @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry["link"])!@@!ansi.freset!@',
        },
    {
        # Weather.com
        # Weather.com has very restricted License Agreement (for cli program),
        # if you don't care about that, please do not use my license key.
        # You find it in clis.py, replace it with yours.
        # Note that you can only use three weather sources (Weather.com's XOAP License Aggrement)
        'type': 'weather',
        #'src_name': 'Weather',
        # Search for locid, visit http://xoap.weather.com/search/search?where=[locationname]
        # For example http://xoap.weather.com/search/search?where=taipei
        # Returns
        #   <search ver="3.0">
        #     <loc id="TWXX0021" type="1">Taipei, Taiwan</loc>
        #   </search>
        # Where TWXX0021 is the locid
        'locid': '***Read above***',
        # Set of units. s for Standard or m for Metric
        #'unit': 'm',
        # Update interval in minutes, must be 25 or greater
        #'interval': 30,
        # There are four promotion links in output (Weather.com's XOAP License Aggrement), please do not remove them.
        #'output': '@!ansi.fgreen!@@!ftime(weather["cc"]["lsup"], "%H:%M:%S")!@@!ansi.freset!@ @!ansi.fred!@[@!src_name!@]@!ansi.freset!@ @!ansi.fyellow!@@!weather["cc"]["obst"]!@@!ansi.freset!@ Temperature: @!weather["cc"]["tmp"]!@°@!weather["head"]["ut"]!@ Feels like: @!weather["cc"]["flik"]!@°@!weather["head"]["ut"]!@ Conditions: @!weather["cc"]["t"]!@ Wind: <!--(if weather["cc"]["wind"]["s"] == "calm")-->calm<!--(else)-->@!weather["cc"]["wind"]["s"]!@@!weather["head"]["us"]!@ (@!int(float(weather["cc"]["wind"]["s"]) * 0.6214)!@mph) (@!weather["cc"]["wind"]["t"]!@)<!--(end)--> (Provided by weather.com; @!weather["lnks"]["link"][0]["t"]!@: @!surl(weather["lnks"]["link"][0]["l"])!@ @!weather["lnks"]["link"][1]["t"]!@: @!surl(weather["lnks"]["link"][1]["l"])!@ @!weather["lnks"]["link"][2]["t"]!@: @!surl(weather["lnks"]["link"][2]["l"])!@ @!weather["lnks"]["link"][3]["t"]!@: @!surl(weather["lnks"]["link"][3]["l"])!@)',
    {
        # PunBB 1.2: Special for PunBB 1.2's feed
        'type': 'punbb12',
        #src_name': 'Feed',
        'feed': 'http://example.com/extern.php?action=active&type=RSS',
        #'interval': 60,
        #'output': '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry.link)!@@!ansi.freset!@',
        },
    {
        # Tail: tail -F
        'type': 'tail',
        #src_name': 'Tail',
        # The file you want to tail
        'file': '~/test.txt',
        #'output': '@!ansi.fgreen!@@!ftime(entry["updated"], "%H:%M:%S")!@@!ansi.freset!@ [@!src_name!@] @!entry["title"]!@ @!ansi.fmagenta!@@!surl(entry.link)!@@!ansi.freset!@',
        # How many last lines to be print when firstly runs
        #'last_lines': 0,
        },
    ]

# The setting of local url shortening server
#server = {
#    'name': 'localhost',
#    'port': 8080,
#    }
  }
