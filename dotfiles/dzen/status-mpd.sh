#!/bin/bash
# $1 is the timeout (`dzen2 -p $1` doesn't seem to work in this script)

width=720
font_pixelsize=16
line_height=$((font_pixelsize + 4))
lines=3
height=$((line_height * (lines + 1) + 5 * 2))

bottom_gap=20
read _ s_width <<< "$(xwininfo -root | egrep Width)"
read _ s_height <<< "$(xwininfo -root | egrep Height)"

[[ $1 -gt 0 ]] && end_time=$(($(date +%s%N) + $1 * 1000000000))

while :; do
# Update last fm play count and cover art
lf-playcount-image.sh
read _ playcount _ _ _ loved </tmp/lf-playcount-image
# Preparing cover art
image_filename="/tmp/lf-images/$(cut -f 4 -d \  "/tmp/lf-playcount-image" | tr -t \/ -)"
image_filename_xpm="${image_filename%.*}.xpm"
[[ ! -f "$image_filename_xbm" ]] && convert -scale 80x80 "$image_filename" "$image_filename_xpm"

echo -n '^ib(1)'
i=0
mpc -f '%artist% - %title% - %album%' | while read line; do
	echo -n "^pa(5;$((i*line_height + 5)))$line"
	((i++))
done
i=3
echo -n "^pa(5;$((i*line_height + 5)))Played $playcount times "
[[ "$loved" == "1" ]] && echo -n "^fg(#a00)" || echo -n "^fg(#444)"
echo -n "♥^fg()"
echo "^pa($((width-80-5));5)^i($image_filename_xpm)"
sleep 1
[[ $1 -gt 0 ]] && [[ $(date +%s%N) > "$end_time" ]] && break
done | dzen2 -x $((s_width - width)) -y $((s_height - height - bottom_gap)) -w $width -h $height -ta left -fn "Envy Code R:pixelsize=$font_pixelsize" -e 'leavetitle=exit;button3=exit;button4=scrollup;button5=scrolldown;onstart=uncollapse'
