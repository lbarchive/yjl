#!/bin/bash
#
# Quick Directory Switcher
#
# GPLv3
#
# Author       : Yu-Jie Lin
# Creation Date: 2007-12-26T03:01:29+0800

G_DIRS=~/.g_dirs

ShowHelp() {
	echo "Commands:
  g -a     : add current directory
  g -a dir : add dir
  g -r     : remove a directory from list
"
	}

ShowDirs() {
	echo Pick one:
	i=0
	for d in $(cat $G_DIRS); do
		echo "$i: $d"
		dir[$i]=$d
		(( i++ ))
	done
	echo;
	}

SortDirs() {
	sort $G_DIRS > $G_DIRS.tmp
	mv -f $G_DIRS.tmp $G_DIRS
	}

# Check commands
if [[ $# > 0 ]]; then
	case "$1" in
		-a|--add|a|add)
			dir=$(pwd)
			[[ "$2" != "" ]] && dir=$2
			egrep "^$dir\$" $G_DIRS &> /dev/null
			[[ $? == 0 ]] && echo "$dir already exists." && exit 1
			echo "$dir" >> $G_DIRS
			echo "$dir added."
			SortDirs
			exit 0
			;;
		-r|--remove|r|remove)
			ShowDirs
			read -p "Which dir to remove? " removed
			rm -f $G_DIRS
			touch $G_DIRS
			for (( i=0; i<${#dir[@]}; i++)); do
				[[ $i != $removed ]] && echo "${dir[$i]}" >> $G_DIRS
			done
			echo "${dir[$removed]} removed."
			exit 0
			;;
		-h|--help|h|help)
			ShowHelp
			exit
			;;
		*)
			echo "Wrong command!"
			echo;
			ShowHelp
			exit 1
			;;
	esac
fi

# Make sure there are some dirs in ~/.g_dirs
if [[ ! -e $G_DIRS ]] || [[ $(wc -l $G_DIRS) == 0* ]]; then
	echo "Please add some directories first!
"
	ShowHelp
	exit 1
fi

ShowDirs
read -p "Which dir? " i

[[ "$i" == "" ]] && exit 1

cd ${dir[$i]}
