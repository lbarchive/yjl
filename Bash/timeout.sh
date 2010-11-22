#!/bin/bash
# Running command with timeout
# Author: Yu-Jie Lin
# BSD license

if (( $# < 2 )); then
	echo "Usage: $(basename $0) <timeout> <command> [arguments]" >&2
	exit 1
fi

end_time=$(bc <<< "$(date +%s.%N) + $1")

trap 'kill $CMD_PID ; exit 130' INT

shift
bash -c "$*" &
CMD_PID=$!

while sleep 0.1; do
	[[ ! -d "/proc/$CMD_PID" ]] && break
	if [[ "$(date +%s.%N)" > "$end_time" ]]; then
		kill $CMD_PID
		exit 255
	fi
done

wait $CMD_PID
