#!/bin/bash
# mp-ctrl.sh A script for media keys to control media players
# Copyright 2009 (c) Yu-Jie Lin
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
# Usage:
#   mp-ctrl command
#     command can be one of
#       play
#       pause
#       stop
#       prev
#       next
#
# Supported players:
#   MPD     : http://mpd.wikia.com/
#   Shell.FM: http://nex.scrapping.cc/shell-fm/
#
# Fluxbox: If you use the following in your ~/.fluxbox/keys:
#	# Media keys for media players
#	# Play
#	Mod4 P :Exec mp-ctrl.sh play
#	# XF86AudioPlay with Pause
#	172 :Exec mp-ctrl.sh pause
#	# XF86AudioPrev
#	173 :Exec mp-ctrl.sh prev
#	# XF86AudioNext
#	171 :Exec mp-ctrl.sh next
#	# XF86AudioStop
#	174 :Exec mp-ctrl.sh stop
#	# Shell.FM Love
#	Mod4 L :Exec mp-ctrl.sh love
#	# Shell.FM Ban
#	Mod4 B :Exec mp-ctrl.sh ban
#
# Author: Yu-Jie Lin (http://livibetter.mp/)
#
# Note: mp-ctrl use pgrep to check if process is running, therefore, it's only
# for local control.

##########
# Settings

# Find the first availble one and control it, the rest will be ignored
SEEK_ORDER="mpd shellfm"

MPD_HOST=localhost
MPD_PORT=6600

SHELLFM_HOST=localhost
SHELLFM_PORT=54311

#################
# End of Settings

MPD_TCP=/dev/tcp/$MPD_HOST/$MPD_PORT
SHELLFM_TCP=/dev/tcp/$SHELLFM_HOST/$SHELLFM_PORT

_ret=

#####
# MPD

function mpd_request() {
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

function mpd_extract_field() {
	# $1 field_name
	# $2 search body
	_ret=$(grep "^$1: " <<< "$2" 2>/dev/null | sed "s/$1: //")
	}

function control_mpd {
	case "$1" in
		play)	mpd_request "play" ;;
		pause)	mpd_request "status"
			mpd_extract_field "state" "$_ret"
			[[ "$_ret" == "pause" ]] && mpd_request "pause 0" || mpd_request "pause 1"
			;;
		stop)	mpd_request "stop" ;;
		prev*)	mpd_request "previous" ;;
		next)	mpd_request "next" ;;
	esac
	}

##########
# Shell.FM

function shellfm_request() {
	# $1 command
	exec 5<> $SHELLFM_TCP 2>/dev/null
	[[ $? -gt 0 ]] && return 1
	echo $1 >&5
	exec 5>&-
	return 0
	}

function control_shellfm {
	case "$1" in
		play)	shellfm_request "play" ;;
		pause)	shellfm_request "pause" ;;
		stop)	shellfm_request "stop" ;;
		next)	shellfm_request "skip" ;;
		love)	shellfm_request "love" ;;
		ban)	shellfm_request "ban" ;;
	esac
	}

######
# Main

for mp in $SEEK_ORDER; do
	case "$mp" in
		mpd)
			pgrep mpd &>/dev/null
			[[ $? -eq 0 ]] && control_mpd $1 && break
			;;
		shellfm)
			pgrep shell-fm &>/dev/null
			[[ $? -eq 0 ]] && control_shellfm $1 && break
			;;
	esac
done
