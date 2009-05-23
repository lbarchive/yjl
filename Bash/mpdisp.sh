#!/bin/bash
# MPDisp
# copyright 2009 (c) Yu-Jie Lin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Keys:
#  p     - Pause/Resume
#  Enter - Play
#  s     - Stop
#  n     - Next song
#  p     - Previous song
#  r     - Repeat mode on/off
#  S     - Single mode on/off
#  R     - Random mode on/off
#  q     - Quit
#  Q     - Quit with MPD
#
# Dependencies:
#  * Figlet (http://www.figlet.org/)
#
# Changelog:
#  2009-05-24: First release

##########
# Settings

HOST=localhost
PORT=6600
# PASSWORD not yet implemented
# Some good choices: sblood, roman, poison, cosmic, cosmike, hollywood
# You can see more at /usr/share/figlet
FONT=slant
# Say C-O-L-O-R-S-!
TITLE_COLOR="\033[1;31m"
ALBUM_COLOR="\033[1;32m"
ARTIST_COLOR="\033[1;34m"
TIME_COLOR="\033[1;35m"

#################
# End of Settings

MPD_TCP=/dev/tcp/$HOST/$PORT
[[ "$FONT" != "" ]] && FONT="-f $FONT"
_ret=
song_title=
song_artist=
song_album=
song_time=
current_time=
song_time_f=
current_time_f=
text_height=

###########
# Functions

function request() {
	# $1 command
	exec 5<> $MPD_TCP 2>/dev/null
	[[ $? -gt 0 ]] && return 1
	echo $1 >&5
	echo "close" >&5
	tmp=$(cat <&5)
	exec 5>&-
	# TODO check OK before return
	_ret=$(head -n -1 <<< "$tmp" | tail -n +2)
	return 0
	}

function extract_field() {
	# $1 field_name
	# $2 search body
	_ret=$(grep "^$1: " <<< "$2" 2>/dev/null | sed "s/$1: //")
	}

function parse_song_info() {
	request currentsong
	[[ $? -gt 0 ]] && return 1
	_tmp=$_ret
	extract_field "Title" "$_tmp"
	song_title=$_ret
	extract_field "Artist" "$_tmp"
	song_artist=$_ret
	extract_field "Album" "$_tmp"
	song_album=$_ret
	extract_field "Time" "$_tmp"
	song_time=$_ret
	fmt_time $song_time
	song_time_f=$_ret
	}

function parse_time() {
	request "status"
	extract_field "time" "$_ret"
	current_time=$(cut -f 1 -d : <<< "$_ret")
	fmt_time $current_time
	current_time_f=$_ret
	}

function fmt_time() {
	# $1 time in second
	(( _mm=$1 / 60 ))
	[[ ${#_mm} -eq 1 ]] && _mm="0$_mm"
	(( _ss=$1 - $_mm * 60 ))
	[[ ${#_ss} -eq 1 ]] && _ss="0$_ss"
	_ret="$_mm:$_ss"
	}

function print_song_info {
	tput clear
	echo -ne $TITLE_COLOR
	echo $song_title | figlet -c -t $FONT
	echo -ne "\033[0m"
	echo -ne $ALBUM_COLOR
	echo $song_album | figlet -c -t $FONT
	echo -ne "\033[0m"
	echo -ne $ARTIST_COLOR
	echo $song_artist | figlet -c -t $FONT
	echo -ne "\033[0m"
	echo -ne "\033[s"
	_song_title=$song_title
	}

function print_time {
	echo -ne "\033[u"
	# Clean up few lines
	for ((i=0; i<$text_height; i++)); do
		echo -e "\033[K"
	done
	echo -ne "\033[u"
	echo -ne $TIME_COLOR
	echo "$current_time_f / $song_time_f" | figlet -c -t $FONT
	echo -ne "\033[0m"
	_current_time=$current_time
	echo
	}

function print_status {
	echo -ne "\x0d\033[K"
	request "status"
	_tmp=$_ret
	extract_field "song" "$_tmp"
	song=$_ret
	extract_field "playlistlength" "$_tmp"
	length=$_ret
	# [ 5 / 100 ] Repeat Single Random => ...+2+3+2+7*3
	# tput cols only gets 80
	(( space_length=($(stty size | cut -f 2 -d ' ') - (${#song} + ${#length} + 28 )) / 2 ))
	echo -ne "\033[${space_length}G"
	echo -n "[ $song / $length ] "
	extract_field "repeat" "$_tmp"
	[[ $_ret -eq 0 ]] && echo -ne "\033[1;30mRepeat\033[39m" || echo -ne "\033[1;31mRepeat\033[0;39m"
	echo -n ' '
	extract_field "single" "$_tmp"
	[[ $_ret -eq 0 ]] && echo -ne "\033[1;30mSingle\033[39m" || echo -ne "\033[1;32mSingle\033[0;39m"
	echo -n ' '
	extract_field "random" "$_tmp"
	[[ $_ret -eq 0 ]] && echo -ne "\033[1;30mRandom\033[39m" || echo -ne "\033[1;34mRandom\033[0;39m"
	}

function sig_winch {
	parse_song_info
	print_song_info
	parse_time
	print_time
	print_status
	}

function quit {
	# Show cursor
	echo -e "\033[?25h"
	# Echo for stdin
	stty echo
	exit $1
	}

######
# Main

# Catch program exiting and keyboard interrupt (Ctrl+C)
trap quit INT EXIT
# Catch window size changing
trap sig_winch WINCH

# No echo for stdin
stty -echo
# Hide cursor
echo -ne "\033[?25l"

# Calculate text's height
_tmp=$(figlet $FONT 0)
text_height=$(wc -l <<< "$_tmp")

# Put displaying in background
while true; do
	parse_song_info
	[[ $? -gt 0 ]] && exit 1
	if [[ "$_song_title" != "$song_title" ]]; then
		print_song_info
		parse_time
		print_time
		print_status
	else
		parse_time
		[[ "$_current_time" != "$current_time" ]] && print_time
	fi
	read -n 1 -t 1 ch
	[[ $? -gt 0 ]] && continue
	case "$ch" in
		p)	request "status"
			extract_field "state" "$_ret"
			[[ "$_ret" == "pause" ]] && request "pause 0" || request "pause 1"
			;;
		# Enter key
		'')	request "play" ;;
		P)	request "previous" ;;
		n)	request "next" ;;
		s)	request "stop" ;;
		r)	request "status"
			extract_field "repeat" "$_ret"
			[[ $_ret -eq 0 ]] && request "repeat 1" || request "repeat 0"
			print_status
			;;
		S)	request "status"
			extract_field "single" "$_ret"
			[[ $_ret -eq 0 ]] && request "single 1" || request "single 0"
			print_status
			;;
		R)	request "status"
			extract_field "random" "$_ret"
			[[ $_ret -eq 0 ]] && request "random 1" || request "random 0"
			print_status
			;;
		Q)	request "kill"
			break
			;;
		q)	break ;;
	esac
done
