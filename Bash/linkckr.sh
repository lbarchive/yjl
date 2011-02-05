#!/bin/bash
# Copyright 2011 Yu-Jie Lin
# New BSD License
#
# Known bug: &, &ampt;, and &<anything>.

xmllint --shell --html "$1" <<<"cat //a[starts-with(@href,'http')]" | egrep -o 'https?:[^"]*' | sort | uniq |
while read url; do
	# curl: -s silent, -I header only, -L follow Location, -m 10 sec timeout, -w output format
	read resp_code eff_url <<<"$(curl -s -I -L -m 10 -w '%{http_code} %{url_effective}\n' "$url" | sed '$q;d')"
	case "$resp_code" in
		2*)
			echo -ne "\e[32;1m"
			;;
		3*)
			echo -ne "\e[34;1m"
			;;
		4*)
			echo -ne "\e[31;1m"
			# TODO 405, should re-check with normal HTTP GET request.
			;;
		5*)
			echo -ne "\e[35;1m"
			;;
		*)
			echo -ne "\e[36;1m"
			;;
	esac
	echo -ne "[${resp_code}]\e[0m $url"
	if [[ "$eff_url" != "$url" ]]; then
		echo -n " -> $eff_url"
	fi
	echo
done
