#!/bin/bash

width=600
font_pixelsize=16
line_height=$((font_pixelsize + 4))
lines=8
height=$((line_height * (lines + 1)))

bottom_gap=20
read _ s_width <<< "$(xwininfo -root | egrep Width)"
read _ s_height <<< "$(xwininfo -root | egrep Height)"

{
echo '^fg(#a00)Calendar^fg()'
day=$(date +%d)
day=${day#0}
cal -3s | sed 's/\(.\{21\}.*\) '$day' \(.*.\{21\}\)/\1 ^fg(#a00)'$day'^fg() \2/;s/^/ /'
echo '^uncollapse()'
} | dzen2 -x $((s_width - width)) -y $((s_height - height - bottom_gap)) -w $width -l $lines -h $line_height -sa left -fn "Envy Code R:pixelsize=$font_pixelsize" -e 'leaveslave=exit;button3=exit;button4=scrollup;button5=scrolldown;onstart=scrollhome' -p
