#!/bin/bash
# Copyright 2010 Yu-Jie Lin
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.
#
# Creation Date: 2010-09-11
# Modified from portage-tree.sh
# Usage: ./portage-treemap.sh > treemap.html

BASE_PATH='/var/db/pkg'
#BASE_PATH='/usr/portage'
#BASE_PATH='/usr/local/portage'
#BASE_PATH='/var/lib/layman/somerepo'

##########

ALL_PKGS=$(ls -d $BASE_PATH/*/* | sed "s_$BASE_PATH/__;s_/_ _")

old_cat1=
old_cat2=

echo '<html>
  <head>
    <script type="text/javascript" src="http://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["treemap"]});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
          var data = new google.visualization.DataTable();
          data.addColumn("string", "Child");
          data.addColumn("string", "Parent");
          data.addColumn("number", "ebuilds");
          data.addColumn("number", "ebuilds color");
          data.addRows(['
echo "[\"Portage Tree [$BASE_PATH]\", null, 0, 0],"

echo "$ALL_PKGS" | while read category package; do
	[[ "$(echo $category | grep -)" == "" ]] && [[ $category != 'virtual' ]] && continue
	pkg_name=$(echo $package | sed 's_\([0-9a-zA-Z]\)-\([0-9]\)_\1 \2_' | cut -d \  -f 1)
	echo "${category/-/ } $pkg_name"
done | uniq -c | while read ebuild_count pkg_cat1 pkg_cat2 pkg_name; do
	[[ $old_cat1 != $pkg_cat1 ]] && echo "[\"[$pkg_cat1]\", \"Portage Tree [$BASE_PATH]\", 0, 0]," && old_cat1=$pkg_cat1
	[[ $old_cat2 != $pkg_cat2 ]] && echo "[\"$pkg_cat1-$pkg_cat2\", \"[$pkg_cat1]\", 0, 0]," && old_cat2=$pkg_cat2
	echo "[\"$pkg_name\", \"$pkg_cat1-$pkg_cat2\", $ebuild_count, $ebuild_count],"
done

echo "[null, \"Portage Tree [$BASE_PATH]\", 0, 0]"
echo '          ]);
          var tree = new google.visualization.TreeMap(document.getElementById("visualization"));
          tree.draw(data, {
		    maxDepth: 2,
			minColor: "#a9e",
			midColor: "#8877d8",
            maxColor: "#75d",
            headerHeight: 15,
            fontColor: "white",
			fontFamily: "monospace",
			fontSize: 9
            });
      }
    </script>
  </head>

  <body>
    <div id="visualization" style="width: 640px; height: 640px;"></div>
  </body>
</html>'

