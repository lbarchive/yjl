#!/bin/bash
# Jamendo Radio
# This script is in Public Domain
#
# Author:
#  2009 Yu-Jie Lin (http://livibetter.mp)
#
# Controls:
#  q, Enter: Next song
#  Ctrl + C: Quit
#
# Dependencies:
#  dialog
#  mplayer
#  wget

radios=(\
4 'Dance/Electro' \
5 'Hiphop' \
6 'Jazz' \
7 'Lounge' \
8 'Pop/Songwriting' \
9 'Rock' \
283 'Metal' \
)

RADIO_URL='http://www.jamendo.com/get2/stream/track/m3u/radio_track_inradioplaylist/?order=numradio_asc&radio_id='

IFS=$'\n'
trap 'echo Bye. ; exit 0' SIGINT

###########
# Functions

function show_radio_menu() {
	tmp=$(mktemp)
	dialog --menu "Select radio" 20 80 20 ${radios[@]} 2> $tmp
	radio=$(cat $tmp)
	rm $tmp
	return $?
	}


function play() {
	clear
	mplayer -msglevel all=5 "$1"
	}

######
# Main

radio=
show_radio_menu
clear

pn=1
while true; do
	f_playlist=$(mktemp)
	wget -q "$RADIO_URL$radio&pn=$pn" -O $f_playlist
	for song in $(cat $f_playlist); do
		[[ ${song:0:1} == "#" ]] && continue
		play "$song"
	done

	rm $f_playlist
	(( pn+=1 ))
	done
