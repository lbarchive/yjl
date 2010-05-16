#!/bin/bash
# Copyright (c) 2010, Yu-Jie Lin
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

TCLI_RC="$HOME/.tcli.rc"

# Source TwitterOAuth.sh

OAuth_sh=$(which TwitterOAuth.sh)
(( $? != 0 )) && echo 'Unable to locate TwitterOAuth.sh! Make sure it is in searching PATH.' && exit 1
source "$OAuth_sh"

usage () {
	echo "
usage: $0 options

OPTIONS:
 -h      Show this message
 -c command
	account_update_profile_image
	statuses_update
 -r in_reply_to_status_id
 -s status
 -f file
"
	}

show_config_help () {
	echo "Please create $TCLI_RC with:
oauth_consumer_key=YOUR_CONSUMER_KEY
oauth_consumer_secret=YOUR_CONSUMER_SECRET

You can register new app to get consumer key and secret at
  http://dev.twitter.com/apps/new
"
	exit 1
	}

load_config () {
	[[ -f "$TCLI_RC" ]] && . "$TCLI_RC" || show_config_help

	[[ "$oauth_consumer_key" == "" ]] && show_config_help
	[[ "$oauth_consumer_secret" == "" ]] && show_config_help

	TO_init

	if [[ "$oauth_token" == "" ]] || [[ "$oauth_token_secret" == "" ]]; then
		TO_access_token_helper
		if (( $? == 0 )); then
			oauth_token=${TO_ret[0]}
			oauth_token_secret=${TO_ret[1]}
			echo "oauth_token='${TO_ret[0]}'" >> "$TCLI_RC"
			echo "oauth_token_secret='${TO_ret[1]}'" >> "$TCLI_RC"
			echo "Token saved."
		else
			echo 'Unable to get access token'
			exit 1
		fi
	fi
	}

main () {
	load_config
	
	tcli_command=
	tcli_status=
	tcli_in_reply_to_status_id=
	tcli_file=
	while getopts "c:s:r:f:h" name
	do
		case $name in
		c)	tcli_command="$OPTARG";;
		s)	tcli_status="$OPTARG";;
		r)	tcli_in_reply_to_status_id="$OPTARG";;
		f)	tcli_file="$OPTARG";;
		h)  usage
			exit 0;;
		?)	usage
			exit 2;;
		esac
	done

	case $tcli_command in
	account_update_profile_image)
		[[ "$tcli_file" == "" ]] && echo 'Requires: -f filename' && exit 1
		TO_account_update_profile_image '' "$tcli_file"
		echo "$TO_ret"
		return $TO_rval
		;;
	statuses_update)
		[[ "$tcli_status" == "" ]] && echo 'Requires: -s "status"' && exit 1
		TO_statuses_update '' "$tcli_status" "$tcli_in_reply_to_status_id"
		echo "$TO_ret"
		return $TO_rval
		;;
	esac
	}

main "$@"
