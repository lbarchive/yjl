#!/bin/bash

SP_LINES=6
SP_TW=80

source status-func.sh

{
print_status_title 'Miscellaneous'

thres=$((7*24*60*60))
ts="$(cat /usr/portage/metadata/timestamp.chk)"
dur=$(($(date +%s) - $(date -d "$ts" +%s)))
td="$(td.sh $((thres-dur)))"

echo -n " Portage: "
((dur>=thres)) && echo -n "T + " || echo -n "T - "
echo "$td"

echo -n " YouTube: "
echo -n "$(ls -1 ~/Videos/livibetter/videos | wc -l)"
echo -n " downloaded / "
echo -n "$(ls -1 ~/Videos/livibetter/queue | wc -l)"
echo -n " queued / "
echo "$(pgrep youtube-dl | wc -l) downloading"

echo

echo "$(./weather.sh TWXX0021)" | sed 's/^/ /'

echo '^uncollapse()'
} |
dzen2 \
	-bg $SP_BG -fg $SP_FG \
	-fn "$SP_FONT" -h $SP_LINE_HEIGHT \
	-x $SP_X -y $SP_Y \
	-w $SP_WIDTH -l $SP_LINES \
	-ta left \
	-e 'leaveslave=exit;button3=exit;button4=scrollup;button5=scrolldown' \
	-p
