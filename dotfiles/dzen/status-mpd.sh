#!/bin/bash
# $1 is the timeout (`dzen2 -p $1` doesn't seem to work in this script)

LF_SUBMIT_CURRENTSONG=/tmp/lf-submit.sh.currentsong
bg_color='#303030'
width=720
font_pixelsize=16
line_height=$((font_pixelsize + 4))
lines=3
height=$((line_height * (lines + 1) + 5 * 2))

bottom_gap=20
read _ s_width <<< "$(xwininfo -root | egrep Width)"
read _ s_height <<< "$(xwininfo -root | egrep Height)"

[[ $1 -gt 0 ]] && end_time=$(($(date +%s%N) + $1 * 1000000000))

COVERART='<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:xlink="http://www.w3.org/1999/xlink"
   width="92" height="80" id="coverart">
  <g id="layer1">
    <image xlink:href="file:///tmp/status-mpd.tmp.png"
       x="12" y="0" id="coverart" />
  </g>
</svg>'

# Heart image from http://openiconlibrary.sourceforge.net/gallery2/?./Icons/emblems/emblem-favorite.png
# 32x32 PNG
LOVED_COVERART='<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:xlink="http://www.w3.org/1999/xlink"
   width="92" height="80" id="coverart">
  <g id="layer1">
    <image xlink:href="file:///tmp/status-mpd.tmp.png"
       x="12" y="0" id="coverart" />
	<image xlink:href="file://'"$PWD"'/icons/emblem-favorite.png"
       x="0" y="48" id="heart" />
  </g>
</svg>'

while :; do
# Update last fm play count and cover art
lf-playcount-image.sh
read _ playcount _ _ _ _ loved </tmp/lf-playcount-image
# Preparing cover art
image_filename="/tmp/lf-images/$(cut -f 4 -d \  "/tmp/lf-playcount-image" | tr -t \/ -)"
image_tmp="/tmp/status-mpd.tmp.png"
image_filename_png="${image_filename%.*}.tmp.png"
image_filename_xpm="${image_filename%.*}.xpm"
if [[ ! -f "$image_filename_xbm" ]]; then
	convert -resize 80x80 "$image_filename" "$image_tmp"
	if [[ "$loved" == "1" ]]; then
		# Using Process Substitution for a FIFO, which inkscape can open and read its content.
		# Inkscape doesn't support standard input.
		inkscape <(echo "$LOVED_COVERART") -b "$bg_color" --export-png="$image_filename_png" &>/dev/null
	else
		inkscape <(echo "$COVERART") -b "$bg_color" --export-png="$image_filename_png" &>/dev/null
	fi
	convert "$image_filename_png" "$image_filename_xpm"
fi

echo -n '^ib(1)'
i=0
if [[ -r "$LF_SUBMIT_CURRENTSONG" ]]; then
	song_title="$(line <"$LF_SUBMIT_CURRENTSONG")"
	song_artist="$(sed '2q;d' "$LF_SUBMIT_CURRENTSONG")"
	line="$song_artist - $song_title"
	echo -n "^pa(5;$((i*line_height + 5)))$line"
else
	mpc -f '%artist% - %title% - %album%' | while read line; do
		echo -n "^pa(5;$((i*line_height + 5)))$line"
		((i++))
	done
fi
i=3
echo -n "^pa(5;$((i*line_height + 5)))Played $playcount times "
echo -n "^pa($((width-92-5));5)^i($image_filename_xpm)"
echo ""
sleep 1
[[ $1 -gt 0 ]] && [[ $(date +%s%N) > "$end_time" ]] && break
done | dzen2 -x $((s_width - width)) -y $((s_height - height - bottom_gap)) -w $width -h $height -bg "$bg_color" -ta left -fn "Envy Code R:pixelsize=$font_pixelsize" -e 'leavetitle=exit;button3=exit;button4=scrollup;button5=scrolldown;onstart=uncollapse'
