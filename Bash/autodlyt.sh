#!/bin/bash
# by Yu-Jie Lin
# BSD license
# 2010-11-10T19:13:46+0800

usage () {
	echo "Usage: $(basename $0) username directory-to-store-everything"
	exit 1
}

USERNAME="$1"
[[ "$USERNAME" == "" ]] && usage
DESTDIR="$2/$1"
[[ "$DESTDIR" == "" ]] && usage

DLPROGNAME='youtube-dl'
DLPROGOPTS='-t'

DLPROG="$(type -p "$DLPROGNAME")"
if [[ "$DLPROG" == "" ]]; then
	echo "Could not find $DLPROGNAME."
	exit 1
fi

[[ ! -d "$DESTDIR" ]] && mkdir -p "$DESTDIR"
[[ ! -d "$DESTDIR/errors" ]] && mkdir -p "$DESTDIR/errors"
[[ ! -d "$DESTDIR/videos" ]] && mkdir -p "$DESTDIR/videos"
[[ ! -d "$DESTDIR/queue" ]] && mkdir -p "$DESTDIR/queue"

# Downloading feed
TMPFILE="$(mktemp)"
DLLOG="$(mktemp)"
wget "http://gdata.youtube.com/feeds/api/users/$USERNAME/newsubscriptionvideos?prettyprint=true&fields=entry(link[@rel='alternate'](@href))" -O "$TMPFILE" &>"$DLLOG"
if (( $? != 0 )) || [[ ! -s "$TMPFILE" ]]; then
	cat "$DLLOG" >> "$DESTDIR/errors/dlfeed"
	cat "$DLLOG" 1>&2
	rm "$DLLOG" "$TMPFILE"
	exit 1
fi

videos="$(grep link "$TMPFILE" | sed 's/.*v=\(.*\)&.*/\1/')"
if [[ -z "$videos" ]]; then
	echo "No videos found." 1>&2
	echo "No videos found. XML:" >> "$DESTDIR/errors/dlfeed"
	cat "$TMPFILE" >> "$DESTDIR/errors/dlfeed"
	rm "$DLLOG" "$TMPFILE"
	exit 1
fi
rm "$DLLOG" "$TMPFILE"

lastvideo="$(cat "$DESTDIR"/last 2>/dev/null)"

for v in $videos; do
	[[ "$lastvideo" == "$v" ]] && break
	[[ ! -f "$DESTDIR/queue/$v" ]] && echo "Queuing $v" && echo "http://www.youtube.com/watch?v=$v" > "$DESTDIR/queue/$v"
done

newlastvideo="$(head -1 <<< "$videos")"
[[ "$newlastvideo" != "$lastvideo" ]] && echo "Updating $DESTDIR/last to $newlastvideo" && echo "$newlastvideo" > "$DESTDIR"/last

videos="$(ls "$DESTDIR"/queue/* 2>/dev/null)"
[[ "$videos" == "" ]] && exit

cd "$DESTDIR/videos"
for v in $videos; do
	# Get the URL of video
	vid="$(basename "$v")"
	url="http://www.youtube.com/watch?v=$vid"

	echo "Downloading $url using $DLPROG..."
	dllog="$("$DLPROG" $DLPROGOPTS "$url")"
	if (( $? != 0 )); then
		# Error on downloading, just write the output to errors directory
		echo "$dllog" > "$DESTDIR/errors/$vid"
		echo "$dllog" 1>&2
	fi
	rm "$v"
done
