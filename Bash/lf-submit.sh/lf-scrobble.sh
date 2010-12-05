#!/bin/bash
# Copyright 2010 Yu-Jie Lin
# BSD License
#
# Only accepts exactly 3 arugments
# <action> <timestamp> <file>
#   action can be "-s|scrobble" or "-n|now_playing"
#   file must have an extension, e.g. foo.m4a, bar.mpg
#   timestamp can be dummy a when action is "-n|now_playing"

(( $# != 3 )) && exit 1

lfs_file="${3%.*}.lfs"

# <file> must exist and .lfs must be readable
[[ ! -f "$3" || ! -r "$lfs_file" ]] && exit 1

check=0
params=()
while read line; do
	[[ $line =~ track.* ]] && ((check++))
	[[ $line =~ artist.* ]] && ((check++))
	params[${#params}]="$line"
done < "$lfs_file"

# Don't have enough information to submit
((check < 2)) && exit 1

[[ $1 =~ -s|scrobble ]] && params[${#params[@]}]="timestamp=$2"

lf-submit.sh "$1" "${params[@]}"
