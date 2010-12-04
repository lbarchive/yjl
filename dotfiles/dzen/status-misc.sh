#!/bin/bash

width=600
font_pixelsize=16
line_height=$((font_pixelsize + 4))
lines=6
height=$((line_height * (lines + 1)))

bottom_gap=20
read _ s_width <<< "$(xwininfo -root | egrep Width)"
read _ s_height <<< "$(xwininfo -root | egrep Height)"

{
echo '^fg(#a00)Miscellaneous^fg()'

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
} | dzen2 -x $((s_width - width)) -y $((s_height - height - bottom_gap)) -w $width -l $lines -h $line_height -sa left -fn "Envy Code R:pixelsize=$font_pixelsize" -e 'leaveslave=exit;button3=exit;button4=scrollup;button5=scrolldown;onstart=scrollhome' -p
