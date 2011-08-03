#!/bin/bash
# Script to show (and delete) safe-deletable cache/temporary files of Portage
# By Yu-Jie Lin

DIRS=(
	/usr/portage/distfiles
	/var/cache/edb
	/var/tmp/{binpkgs,ccache,portage} 
	)

# show the space usages
du -sh "${DIRS[@]}"

echo "****************************************"
for d in "${DIRS[@]}"; do
	printf "Delete  %-30s?" "${d}/*"
	read ans
	if [[ "$ans" =~ [yY] ]]; then
		rm -rf "${d}"/*
	fi
done
