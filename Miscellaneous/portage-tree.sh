#!/bin/bash
# Copyright 2010 Yu-Jie Lin
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.
#
# Creation Date: 2010-09-10
# Modified from pkg-wheel.sh
# Requires: Graphviz
# Usage: ./pkg-wheel.sh | dot -Tsvg -ofilename.svg

BASE_PATH='/var/db/pkg'
#BASE_PATH='/usr/portage'
#BASE_PATH='/usr/local/portage'
#BASE_PATH='/var/lib/layman/somerepo'

##########

ALL_PKGS=$(ls -d $BASE_PATH/*/* | sed "s_$BASE_PATH/__;s_/_ _")

old_cat1=
old_cat2=
old_name=

echo 'digraph G{'
echo 'nodesep=0.02'
echo 'ROOT [label="",shape=none,width=0.01,height=0.02]'

echo "$ALL_PKGS" | while read category package; do
	[[ "$(echo $category | grep -)" == "" ]] && [[ $category != 'virtual' ]] && continue
	pkg_cat1=$(echo $category | cut -d - -f 1)
	pkg_cat2=$(echo $category | cut -d - -f 2)
	package=$(echo $package | sed 's_\([0-9a-zA-Z]\)-\([0-9]\)_\1 \2_')
	pkg_name=$(echo $package | cut -d \  -f 1)
	# pkg_ver=$(echo $package | cut -d \  -f 2)

	[[ $old_cat1 != $pkg_cat1 ]] && echo "\"c-$pkg_cat1\"[label=\"\",shape=none,width=0.01,height=0.02]" && old_cat1="$pkg_cat1" && echo "ROOT->\"c-$pkg_cat1\"[dir=none]"
	[[ $old_cat2 != $pkg_cat2 ]] && echo "\"c-$pkg_cat1-$pkg_cat2\"[label=\"\",shape=none,width=0.01,height=0.02]" && echo "\"c-$pkg_cat1\"->\"c-$pkg_cat1-$pkg_cat2\"[dir=none]" && old_cat2="$pkg_cat2"
	[[ $old_name != $pkg_name ]] && echo "\"p-$pkg_cat1-$pkg_cat2-$pkg_name\"[label=\"\",shape=none,width=0.01,height=0.02]" && echo "\"c-$pkg_cat1-$pkg_cat2\"->\"p-$pkg_cat1-$pkg_cat2-$pkg_name\"[dir=none]" && old_name="$pkg_name"
done

echo '}'
