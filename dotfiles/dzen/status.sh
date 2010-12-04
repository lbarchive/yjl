#!/bin/bash
# Copyright 2010 Yu-Jie Lin
# BSD License
# 
#  * update_cpu() is a partially ported version of gcpubar.c from dzen source
#    code, which is licensed under the MIT/X Consortium License,
#    copyright Robert Manea.

# Configuration
###############

BG='#303030'
FG='#aaa'
FONT='Envy Code R-9'

# UI = update interval, PAD is for padding nano seconds
PAD="000000000"
ui_cpu="1$PAD"
ui_mem="10$PAD"
ui_fs="60$PAD"
ui_thm="10$PAD"
ui_sound="200000000"
ui_clock="1$PAD"
ui_mpd="1$PAD"
# Controlling final refresh rate, the following is 0.2 seconds
ui_output="200000000"

# Interval of each iteration of main loop, should be equal to or smaller than $ui_output
SLEEP=0.2

# Should not be changed
ui_network="1$PAD"
unset PAD

# Components update functions
#############################

update_cpu () {
	# Ported from gcpubar.c
	local ncpu cpu_val cpu_maxval
	# 0 1:user 2:unice 3:sys 4:idle 5:iowait
	ncpu=($(grep 'cpu ' /proc/stat))
	
	ncpu[1]=$((ncpu[1]+ncpu[2]))
	cpu_val=$((ncpu[1]-ocpu[1] + ncpu[3]-ocpu[3] + ncpu[5]-ocpu[5]))
	cpu_maxval=$((cpu_val + ncpu[4]-ocpu[4]))

	cpu_percentage=$((100 * cpu_val / cpu_maxval))

	ocpu=("${ncpu[@]}")

	printf -v cpu_dzen "^ca(1,./status-cpu.sh)^i(icons/cpu.xbm)^ca() %3s%%" $cpu_percentage
	update_next_ts cpu
	}

update_mem () {
	read _ _ mem_used mem_free <<< "$(free -b | grep -)"
	
	mem_total=$((mem_used + mem_free))
	mem_used_MB=$((mem_used / 1024 / 1024))
	mem_used_percentage=$((100 * mem_used / mem_total))

	printf -v mem_dzen "^ca(1,./status-mem.sh)^i(icons/mem.xbm)^ca() %sMB %s%%" ${mem_used_MB} ${mem_used_percentage}

	update_next_ts mem
	}

update_fs () {
	# 0:dev 1:size 2:used 3:free 4:percentage 5:mount point
	read _ _ fs_root_used _ fs_root_percentage _ <<< "$(df -h / | tail -1)"

	fs_dzen="^ca(1,./status-fs.sh)^i(icons/diskette.xbm)^ca() ${fs_root_used}B $fs_root_percentage"

	update_next_ts fs
	}

update_thm () {
	read _ thm _ </proc/acpi/thermal_zone/THM/temperature
	thm_dzen="^i(icons/temp.xbm) ${thm}°C"

	update_next_ts thm
	}

update_clock () {
	clock_dzen="^ca(1,./status-clock.sh)^i(icons/clock.xbm)^ca() $(date +'%A, %B %d, %Y %H:%M:%S')"

	update_next_ts clock
	}

update_sound () {
	read _ _ _ _ volume _ sound_enabled <<< "$(amixer get Master | grep 'Front Left:')"

	volume=${volume#[}
	volume=${volume%]}
	sound_enabled=${sound_enabled#[}
	sound_enabled=${sound_enabled%]}

	sound_dzen="^ca(1,urxvtc -name 'dzen-status-sound' -title 'Sound Mixer' -geometry 160x40 -e alsamixer)^i(icons/spkr_01.xbm)^ca() "
	[[ "$sound_enabled" == "on" ]] && sound_dzen="$sound_dzen^fg(#0a0)" || sound_dzen="$sound_dzen^fg(#a00)"
	sound_dzen="$sound_dzen$volume^fg()"

	update_next_ts sound
	}

update_network () {
	local ifx=ppp0 n_rxb n_txb
	read n_rxb < /sys/class/net/$ifx/statistics/rx_bytes
	read n_txb < /sys/class/net/$ifx/statistics/tx_bytes
	rx_rate=$(((n_rxb - rxb) / 1024))
	tx_rate=$(((n_txb - txb) / 1024))
	rxb=$n_rxb
	txb=$n_txb

	printf -v network_dzen "^i(icons/net_wired.xbm) %3s/%3s KB/s" $tx_rate $rx_rate
	update_next_ts network
	}

update_mpd () {
	local mpd_text
	pgrep mpd &>/dev/null && {
		mpd_text="$(mpc -f '[%title% [- %artist%]]' | head -1)"
		printf -v mpd_dzen "^ca(1,./status-mpd.sh)^i(icons/note.xbm) ^fg(#aa0)%-32s^fg()^ca()" "${mpd_text::32}"
		if [[ "$mpd_text" != "$old_mpd_text" ]]; then
			# New song, popup info box!
			killall status-mpd.sh &>/dev/null
			./status-mpd.sh 10 &
			old_mpd_text="$mpd_text"
		fi
	} || {
		mpd_dzen="^ca(1,mpd;mpdscribble)^fg(#888)^i(icons/note.xbm)^fg()^ca()"
	}
	update_next_ts mpd
	}

# Controlling timestamp functions
#################################

update_ts_current () {
	ts_current=$(date +%s%N)
	}

update_next_ts () {
	# $1 is the variable name
	eval "next_$1=\$((ts_current+ui_$1))"
	}

# Initialization
################

cd ~/.dzen

update_ts_current
update_cpu
update_mem
update_fs
update_network
update_thm
update_clock
update_sound
update_mpd

# Main loop
###########

read _ s_width <<< "$(xwininfo -root | egrep Width)"

while :; do
	update_ts_current
	# Time to output?
	if [[ "$next_output" < "$ts_current" ]]; then
		# Update each component
		[[ "$next_cpu" < "$ts_current" ]] && update_cpu
		[[ "$next_mem" < "$ts_current" ]] && update_mem
		[[ "$next_fs" < "$ts_current" ]] && update_fs
		[[ "$next_network" < "$ts_current" ]] && update_network
		[[ "$next_thm" < "$ts_current" ]] && update_thm
		[[ "$next_sound" < "$ts_current" ]] && update_sound
		[[ "$next_clock" < "$ts_current" ]] && update_clock
		[[ "$next_mpd" < "$ts_current" ]] && update_mpd

		# Composing a new output
		output="$cpu_dzen $mem_dzen $fs_dzen $network_dzen $thm_dzen $mpd_dzen $sound_dzen $clock_dzen ^ca(1,./status-misc.sh)^i(icons/info_01.xbm)^ca()"
		[[ "$last_output" != "$output" ]] && echo "$output" && last_output=output
		update_next_ts output
	fi
	sleep $SLEEP
done | dzen2 -bg "$BG" -fg "$FG" -fn "$FONT" -w $((s_width / 2)) -x $((s_width / 2)) -y -1 -ta right -e 'button3=;onstart=lower'
