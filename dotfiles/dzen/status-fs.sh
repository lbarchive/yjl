#!/bin/bash

width=600
font_pixelsize=16
line_height=$((font_pixelsize + 4))
lines=10
height=$((line_height * (lines + 1)))

bottom_gap=20
read _ s_width <<< "$(xwininfo -root | egrep Width)"
read _ s_height <<< "$(xwininfo -root | egrep Height)"

{
echo '^fg(#a00)Filesystems Status^fg()'
df -h | while read fs size used avail usep mountp; do
	if [[ "$fs" == "Filesystem" ]]; then
		# Header
		printf "^fg(#00a)%-10s %8s %8s %8s %8s %-10s^fg()\n" "$fs" $size $used $avail $usep "$mountp"
	else
		printf "^fg(#aaa)%-10s %8s %8s %8s %8s %-10s^fg()\n" "$fs" $size $used $avail $usep "$mountp"
	fi
done
echo '^uncollapse()'
} | dzen2 -x $((s_width - width)) -y $((s_height - height - bottom_gap)) -w $width -l $lines -h $line_height -sa center -fn "Envy Code R:pixelsize=$font_pixelsize" -e 'leaveslave=exit;button3=exit;button4=scrollup;button5=scrolldown;onstart=scrollhome' -p
