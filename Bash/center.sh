#!/bin/bash
# A simple script to align text (with ANSI color codes) at center of terminal
# This script is in Public Domain
# Author: Yu-Jie Lin (http://livibetter.mp/)

IFS=$'\n'
POS=

while read line; do
	if [[ "$POS" == "" ]]; then
		_tmp=$line
		_tmp=$(tr "\033" "$" <<< $_tmp | sed -e "s/$\[[0-9;]*m//g")
		#_width=$(stty size | cut -f 2 -d ' ')
		_width=$(tput cols)
		POS=$(( ($_width - ${#_tmp}) / 2))
		unset _tmp _width
	fi
	echo -ne "\033[${POS}G"
	echo -e "$line"
done
