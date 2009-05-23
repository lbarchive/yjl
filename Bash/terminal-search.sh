#!/bin/bash
# A script to search text from X clipboard

# Or http://search.yahoo.com/search?p=
# Or http://search.live.com/results.aspx?q=
SEARCH_ENGINE="http://www.google.com/search?q="
# Or use firefox, opear, etc
LAUNCHER=xdg-open

text=$(xsel -o)
text=$(python -c """import urllib ; print urllib.quote('$text')""")
$LAUNCHER "$SEARCH_ENGINE$text"
