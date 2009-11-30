#!/bin/bash
# search-result-count: Gets the result count from Google AJAX Search API
#
# Author: Yu-Jie Lin [http://livibetter.com/]
# Last Updated: 2009-11-28T08:04:28+0800
#
# This Bash script is put to Public Domain, use at your own risk.
#
# Depends:
#   wget
#   Google AJAX Search API
#   Yahoo! Search BOSS
#   Bing API
# 	Google Visualization API
#
# Usage: search-result-count keyword [render [width [height]]
#
# 1) Use cron to run daily:
#   search-result-count <keyword>
#
#   It will store a record to CSV file at $HOME/.search-result-count-<keyword>
#
#   Suggest to run every 3 hours:
#   #Mins   Hours   Days    Months  Day of the week
#   0       */3     *       *       *               /path/to/search-result-count <keyword>
#
# 2) Run the following to get rendered html:
#   search-result-count render
#
# You can also specify the width and height of generated timeline chart. The
# rendered HTML will be stored at your home directory with this filename format
# $HOME/search-result-count-<keyword-YYYY-MM-DD.html
#
# Note that this script can not do urlencode for your keyword.

YAHOO_APPID="k7NNT8DV34HFckFK7ZYLD6Ou7MvAW2mqnAi16suw41dvIqOV0OmI6wdf0ot4EyBEDg--"
BING_APPID="F102804AE27C06275E0B535689E4134DABC92FBA"

# Also can set to "allmaximized" but you may get confused at first.
# Read http://j.mp/5IOCWG
SCALE_TYPE="maximized"

get_count() {
	today="$(date +'%Y,%m,%d')"

	# Have we run today?
	[[ -f "$filename" ]] && grep "$today" "$filename" > /dev/null
	[[ $? == 0 ]] && exit 1

	# Get the count
	g_count=$(wget -q "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=$keyword" -O - | egrep -o '"estimatedResultCount":"[0-9]+"' | cut -d\" -f 4)
	[[ $g_count == "" ]] && echo "$(date) Can get Google Search result count for $keyword" >> $HOME/search-result-count.error && exit 1
	y_count=$(wget -q "http://boss.yahooapis.com/ysearch/web/v1/$keyword?appid=$YAHOO_APPID&format=xml" -O - | egrep -o ' totalhits="[0-9]+"' | cut -d\" -f 2)
	[[ $y_count == "" ]] && echo "$(date) Can get Yahoo Search result count for $keyword" >> $HOME/search-result-count.error && exit 1
	b_count=$(wget -q "http://api.bing.net/json.aspx?AppId=$BING_APPID&Version=2.2&Market=en-US&Query=$keyword&Sources=web&Web.Count=1" -O - | egrep -o '"Total":[0-9]+' | cut -d: -f 2)
	[[ $b_count == "" ]] && echo "$(date) Can get Blog Search result count for $keyword" >> $HOME/search-result-count.error && exit 1
	
	[[ ! -f "$filename" ]] && echo "Year,Month,Day,Count" > "$filename"
	echo "$today,$g_count,$y_count,$b_count" >> "$filename"
	}

render() {
	[[ ! -f "$filename" ]] && echo "CSV file $filename do not exist!" && exit 1
	echo -n "Generating... "
	old_IFS=$IFS
	IFS=","
	data=$(cat "$filename" | { data="" ; while read y m d g_count y_count b_count; do
		[[ "$y" == "Year" ]] && continue
		(( m -= 1 ))
		data="$data          [new Date($y, $m, $d), $g_count, "
		[[ $y_count != "" ]] && data="$data $y_count, " || data="$data undefined,"
		[[ $b_count != "" ]] && data="$data $b_count" || data="$data undefined"
		data="$data],\n"
		done
		echo -ne "$data"
		})
	IFS=old_IFS
	echo -n "<html>
  <head>
    <title>Search Result Count for Keyword &#8220$keyword&#8221</title>
    <script type='text/javascript' src='http://www.google.com/jsapi'></script>
    <script type='text/javascript'>
      google.load('visualization', '1', {'packages':['annotatedtimeline']});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'Date');
        data.addColumn('number', 'Google');
        data.addColumn('number', 'Yahoo');
        data.addColumn('number', 'Bing');
        data.addRows([
$data
          [undefined, undefined, undefined, undefined]
        ]);

        var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('chart_div'));
        chart.draw(data, {scaleType: '$SCALE_TYPE'});
      }
    </script>
  </head>
  <body style='text-align: center;'>
    <h1>Keyword &#8220$keyword&#8221</h1>
    <div id='chart_div' style='width: ${width}px; height: ${height}px; margin: 0 auto;'></div>
  </body>
</html>" > "$out_filename"
	echo "done."
	}

# Main
[[ $1 == "" ]] && exit 1
keyword="$1"
filename="$HOME/.search-result-count-$1"

if [[ $2 == "render" ]]; then
	out_filename="$HOME/search-result-count-$1-$(date +'%Y-%m-%d').html"
	[[ $3 == "" ]] && width=1280 || width="$3"
	[[ $4 == "" ]] && height=720 || height="$4"
	render
else
	get_count
fi
