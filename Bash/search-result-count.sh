#!/bin/bash
# search-result-count: Gets the result count from Google AJAX Search API
#
# Author: Yu-Jie Lin [http://livibetter.com/]
# Last Updated: 2009-11-26T12:23:47+0800
#
# This Bash script is put to Public Domain, use at your own risk.
#
# Depends:
#   wget
#   Google AJAX Search API
# 	Google Visualization API
#
# Usage: search-result-count keyword [render [width [height]]
#
# 1) Use cron to run daily:
#   search-result-count <keyword>
#
#   It will store a record to CSV file at $HOME/.search-result-count-<keyword>
#
# 2) Run the following to get rendered html:
#   search-result-count render
#
# You can also specify the width and height of generated timeline chart. The
# rendered HTML will be stored at your home directory with this filename format
# $HOME/search-result-count-<keyword-YYYY-MM-DD.html
#
# Note that this script can not do urlencode for your keyword.

get_count() {
	today="$(date +'%Y,%m,%d')"

	# Have we run today?
	[[ -f "$filename" ]] && grep "$today" "$filename" > /dev/null
	[[ $? == 0 ]] && exit 1

	# Get the count
	count=$(wget -q "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=$keyword" -O - | egrep -o '"estimatedResultCount":"[0-9]+"' | cut -d\" -f 4)

	if [[ $count != "" ]]; then
		[[ ! -f "$filename" ]] && echo "Year,Month,Day,Count" > "$filename"
		echo "$today,$count" >> "$filename"
	fi
	}

render() {
	[[ ! -f "$filename" ]] && echo "CSV file $filename do not exist!" && exit 1
	echo -n "Generating... "
	old_IFS=$IFS
	IFS=","
	data=$(cat "$filename" | { data="" ; while read y m d count; do
		[[ "$y" == "Year" ]] && continue
		(( m -= 1 ))
		data="$data          [new Date($y, $m, $d), $count],\n"
		done
		echo -ne "$data"
		})
	IFS=old_IFS
	echo -n "<html>
  <head>
    <title>Google Search Result Count for Keyword &#8220$keyword&#8221</title>
    <script type='text/javascript' src='http://www.google.com/jsapi'></script>
    <script type='text/javascript'>
      google.load('visualization', '1', {'packages':['annotatedtimeline']});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'Date');
        data.addColumn('number', '$keyword');
        data.addRows([
$data
          [undefined, undefined]
        ]);

        var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('chart_div'));
        chart.draw(data);
      }
    </script>
  </head>
  <body style='text-align: center;'>
    <h1>Google Search Result Count for Keyword &#8220$keyword&#8221</h1>
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
