sources = [
    {
        # Twitter: Statuses of you and whom you follow
        'type': 'twitter',
        'username': 'yourname', 
        'password': 'secret', 
        'interval': 60, 
        'output': '[%(src_name)s] %(ansi_fgreen)s%(created_at)s%(ansi_freset)s %(user_screen_name)s: %(text)s %(link)s',
        'date_fmt': '%H:%M:%S',
        },
    {
        # FriendFeed: Entries of you home
        'type': 'friendfeed',
        'nickname': 'yourname',
        'remote_key': 'secret',
        'interval': 60,
        'output': '[%(src_name)s] %(ansi_fgreen)s%(updated)s%(ansi_freset)s E %(user_nickname)s: %(room)s%(title)s %(entry_link)s',
        'output_like': '[%(src_name)s] %(ansi_fgreen)s%(date)s%(ansi_freset)s L %(user_nickname)s: %(title)s %(entry_link)s',
        'output_comment': '[%(src_name)s] %(ansi_fgreen)s%(date)s%(ansi_freset)s C %(user_nickname)s on %(title)s: %(body)s %(entry_link)s',
        'show_like': True,
        'show_comment': True,
        'date_fmt': '%H:%M:%S',
        },
    {
        # Feed: Normal feed
        'type': 'feed',
        'feed': 'http://search.twitter.com/search.atom?q=twitter',
        'interval': 60,
        'output': '[%(src_name)s] %(ansi_fgreen)s%(updated)s%(ansi_freset)s %(title)s %(link)s',
        'date_fmt': '%H:%M:%S',
        },
    {
        # GMail: Mails in inbox
        'type': 'gmail',
        'email': 'yourname@gmail.com',
        'password': 'secret',
        'interval': 60,
        'output': '[%(src_name)s] %(ansi_fgreen)s%(updated)s%(ansi_freset)s %(author_name)s: %(title)s %(link)s',
        'date_fmt': '%H:%M:%S',
        },
    {
        # Google Reader: Items of subscriptions
        'type': 'greader',
        'email': 'yourname@gmail.com',
        'password': 'secret',
        'interval': 60,
        'output': '[%(src_name)s] %(ansi_fgreen)s%(updated)s%(ansi_freset)s %(source_title)s: %(title)s %(link)s',
        'date_fmt': '%H:%M:%S',
        },
    ]
