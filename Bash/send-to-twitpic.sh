#!/bin/bash
# Upload photo to TwitPic.com
# 2010-04-03T23:19:23+0800

if [[ ! -f "$1" ]]; then
	echo "Usage: $0 <image>"
	exit 1
fi

read -e -p "Twitter Username: " ID
read -s -p "Twitter Password: " PW
echo
read -p "Also post to twitter Account [Y/n]? " result
echo

if [[ $result == "" || $result == "y" || $result == "Y" ]]; then
	read -e -p "Message: " message
	echo
	curl -F "media=@$1" -F "username=$ID" -F "password=$PW" -F "message=$message" http://twitpic.com/api/uploadAndPost
else
	echo
	curl -F "media=@$1" -F "username=$ID" -F "password=$PW" http://twitpic.com/api/upload
fi
echo
