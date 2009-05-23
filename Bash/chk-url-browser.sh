#!/bin/bash
# A script to check if select a url, if so, then open it in browser

# Or http://search.yahoo.com/search?p=
# Or http://search.live.com/results.aspx?q=
SEARCH_ENGINE="http://www.google.com/search?q="
# Or use firefox, opear, etc
LAUNCHER=xdg-open

url=$(xsel -o)
[[ $(egrep "(ht|f)tps?://" <<< $url) ]] || exit 1
$LAUNCHER "$url"
