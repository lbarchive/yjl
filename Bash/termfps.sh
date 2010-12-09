#!/bin/bash
# Copyright 2010 Yu-Jie Lin
# BSD License
#
# Usage: termfps.sh [FRAMES] [COLUMNS] [LINES]

FRAMES=${1:-100}
COLUMNS=${2:-$(tput cols)}
LINES=${3:-$(tput lines)}

printf -v dummy_line "%${COLUMNS}s" ''
printf -v dummy_line_n "%${COLUMNS}s\n" ''
printf -v dummy_frame "%$((LINES-1))s" ''

for ((ch=0;ch<10;ch++)); do
	line_str=${dummy_line// /$ch}
	line_n_str=${dummy_line_n// /$ch}
	frame_str="${dummy_frame// /$line_n_str}$line_str"
	frame_str_r="frame_str$ch"
	
	eval "$frame_str_r=\"$frame_str\""
done

t_start=$(date +%s.%N)
for ((i=0;i<FRAMES;i++)); do
	for ((ch=0;ch<10;ch++)); do
		frame_str="frame_str$ch"
		echo -ne "\033[H${!frame_str}"
	done
done
t_end=$(date +%s.%N)

echo
echo "For ${COLUMNS}x${LINES} $FRAMES frames, elapsed time: $(bc <<< "scale=3 ; ($t_end-$t_start)/1") seconds"
echo -n "Frames per second: "
bc <<< "scale=3 ; $FRAMES/($t_end-$t_start)"
