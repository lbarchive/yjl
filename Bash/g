#!/bin/bash
#
# g - Quick Directory Switcher
#
# Copyright (C) 2008, 2009 Yu-Jie Lin
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
#
# Author       : Yu-Jie Lin
# Website      : http://code.google.com/p/yjl/wiki/BashGscript
# Creation Date: 2007-12-26T03:01:29+0800

# Which file to store directories
G_DIRS=~/.g_dirs

# Shows help information
G_ShowHelp() {
	echo "Commands:
  g #          : change working directory to dir#
  g dir        : change working directory to dir
  g (-g|g)     : get a list of directories
  g (-a|a)     : add current directory
  g (-a|a) dir : add dir
  g (-c|c)     : clean up non-existing directories
  g (-r|r)     : remove a directory from list
  g (-h|h)     : show what you are reading right now
"
	}

# Shows stored directories
G_ShowDirs() {
	[[ $1 == "" ]] && echo Pick one:
	i=0
	for d in $(cat $G_DIRS); do
		[[ $1 == "" ]] && echo "$i: $d"
		dir[$i]=$d
		(( i++ ))
	done
	echo;
	}

# Sorts directories after adding or removing
G_SortDirs() {
	sort $G_DIRS > $G_DIRS.tmp
	mv -f $G_DIRS.tmp $G_DIRS
	}

# The main function
g() {
	[[ -d $1 ]] && cd $1 && return 0
	# Check commands
	if [[ $# > 0 ]]; then
		case "$1" in
			-a|--add|a|add)
				dir=$(pwd)
				[[ "$2" != "" ]] && dir=$2
				egrep "^$dir\$" $G_DIRS &> /dev/null
				[[ $? == 0 ]] && echo "$dir already exists." && return 1
				echo "$dir" >> $G_DIRS
				echo "$dir added."
				G_SortDirs
				return 0
				;;
			-c|--clean|c|clean)
				G_ShowDirs 1
				echo -n "cleaning up..."
				rm -f $G_DIRS
				touch $G_DIRS
				for (( i=0; i<${#dir[@]}; i++)); do
					[[ -d ${dir[$i]} ]] && echo "${dir[$i]}" >> $G_DIRS
				done
				echo "done."
				return 0
				;;
			-r|--remove|r|remove)
				G_ShowDirs
				read -p "Which dir to remove? " removed
				[[ $removed == "" ]] && return 1
				rm -f $G_DIRS
				touch $G_DIRS
				for (( i=0; i<${#dir[@]}; i++)); do
					[[ $i != $removed ]] && echo "${dir[$i]}" >> $G_DIRS
				done
				echo "${dir[$removed]} removed."
				return 0
				;;
			-h|--help|h|help)
				G_ShowHelp
				return 0
				;;
			-g|--go|g|go)
				;;
			*)
				if [[ $(egrep "^[0-9]+$" <<< $1) ]]; then
					G_ShowDirs > /dev/null
					if [[ $1 -ge 0 && $1 -lt ${#dir[@]} ]]; then
						cd ${dir[$1]}
						return 0
					fi
				fi
				echo "Wrong command!"
				echo;
				G_ShowHelp
				return 1
				;;
		esac
	fi

	# Make sure there are some dirs in ~/.g_dirs
	if [[ ! -e $G_DIRS ]] || [[ $(wc -l $G_DIRS) == 0* ]]; then
		echo "Please add some directories first!
"
		G_ShowHelp
		return 1
	fi

	G_ShowDirs
	read -p "Which dir? " i
	[[ $i == "" ]] && return 1

	cd ${dir[$i]}
	}

# The Bash completion function
_g() {
	# Make sure we have $G_DIRS
	[[ ! -e $G_DIRS ]] && return 1

    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts=$(cat $G_DIRS)

	# Only do completion for once
	for opt in $opts; do
		[[ $prev == $opt ]] && return 1
	done
	COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
	return 0
	}

# If this script is sourced or run without arguments, it will think to be run
# as Bash function.
if [[ $# > 0 ]]; then
	g $*
else
	complete -F _g g
fi
