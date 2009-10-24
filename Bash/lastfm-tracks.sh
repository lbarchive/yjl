#!/bin/bash
# Downloads Last.fm top track feeds and uses XSLT to transform to the format
# which Blogger profile uses
#
# Saves two files
#   lastfm-tracks.xml - Download from Last.fm
#   lastfm-tracks-result.txt - Result text file for being pasted to Blogger
#
# Requires
#   xsltproc
#   wget
#
# Author: Yu-Jie Lin ( http://livibetter.mp/ )


read -p "Your Last.fm username: " username

TRACKS_XML="http://ws.audioscrobbler.com/2.0/user/$username"

echo "
Choose period of your top tracks:
 1 - Last 7 Days
 2 - Last 3 Months
 3 - Last 6 Months
 4 - Last 12 Months
 Other - Overall
"
read -p "Select? " period

case $period in
	1)
		TRACKS_XML="$TRACKS_XML/weeklytrackchart.xml"
		;;
	2)
		TRACKS_XML="$TRACKS_XML/toptracks.xml?period=3month"
		;;
	3)
		TRACKS_XML="$TRACKS_XML/toptracks.xml?period=6month"
		;;
	4)
		TRACKS_XML="$TRACKS_XML/toptracks.xml?period=12month"
		;;
	*)
		TRACKS_XML="$TRACKS_XML/toptracks.xml"
		;;
esac

wget "$TRACKS_XML" -O lastfm-tracks.xml
[[ $? > 0 ]] && exit 1

RESULT_TXT="lastfm-track-result.txt"
xsltproc -o "$RESULT_TXT" lastfm-tracks.xslt lastfm-tracks.xml

[[ $? > 0 ]] && exit 1

echo "===== BEGIN ====="
cat "$RESULT_TXT"
echo
echo "====== END ======"
echo "
You can also open the result text file $RESULT_TXT.
"
