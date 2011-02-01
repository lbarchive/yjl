#!/bin/bash
# Copyright 2010, 2011 Yu-Jie Lin
# BSD License

# Find real mplayer command
mplayer_cmd="$(which -a mplayer | grep 'usr.*bin' | head -1)"

if [[ -z "$mplayer_cmd" ]]; then
	echo "Can not find mplayer!" >&2
	exit 1
fi

# a file is played repeatly, happened with SMPlayer single file repeat, need
# msglevel 6 to know when new start happens.
[[ "${@:$#-2}" =~ '-loop '[0-9]+ ]] && is_loop=1 && msglevel='-msglevel all=6'

{ "$mplayer_cmd" "$@" $msglevel ; echo -n $'\r' ; } | while read -d $'\r' block; do
	# Finding newly played file
	while read line; do
		if [[ $line =~ Playing.* ]]; then
			new_file=${line:8:${#line}-9} && new_ts=$(date +%s)
		elif [[ $is_loop -eq 1 && $line =~ 'loop_times = '.* ]]; then
			# It's a new round
			new_file="$last_file"
			new_ts=$(date +%s)
		elif [[ $line =~ Exiting.* ]]; then
			[[ $line =~ .*'End of file'.* ]] && lf-scrobble.sh -s $last_ts "$last_file" &
			echo
		fi
	done <<< "$block"

	if [[ ! -z "$new_file" ]]; then
		{
			# Scrobbling last_file
			# FIXME: If user skip file, the file is still submitted, it
			# shouldn't be.
			[[ ! -z "$last_file" ]] && lf-scrobble.sh -s $last_ts "$last_file"
			# Submitting now playing on new_file
			lf-scrobble.sh -n $new_ts "$new_file"
		} &
		last_file="$new_file"
		last_ts="$new_ts"
		new_file=
		new_ts=
	fi
	echo -n "$block"$'\r'
done
rm "/tmp/lf-submit.sh.currentsong" &>/dev/null
echo
