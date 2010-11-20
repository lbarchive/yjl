#!/bin/bash
# Calculating merge time from last `emerge` run.
# Copyright 2010 Yu-Jie Lin
# Licensed under the BSD

LOGFILE=/var/log/emerge.log

[[ ! -r "$LOGFILE" ]] && echo "You do not have permission to open $LOGFILE. Please run as root." 1>&2 && exit 1

sed -n '
/Started emerge on/ {s/\([0-9]\+\):.*/\1/;h}
/>>> emerge/ {s/\([0-9]\+\):.*) \(.\+\) to .*/\1 \2/;H}
/\(::: completed emerge\|\*\*\* exiting unsuccessfully\)/ {s/\([0-9]\+\):  \(:::\|\*\*\*\).*/\1 \2/;H}
$ {x;p}
' "$LOGFILE" | awk '
function plural (n) {
	if (n==1) return "";
	return "s";
	}
function hrtime (s) {
	ss = s%60;
	mm = int(s/60%60);
	hh = int(s/3600);
	t="";
	if (hh>0) t=t sprintf("\033[32;1m%d\033[0m hour%s ", hh, plural(hh));
	if (mm>0) t=t sprintf("\033[32;1m%d\033[0m minute%s ", mm, plural(mm));
	if (ss>0) t=t sprintf("\033[32;1m%d\033[0m second%s", ss, plural(ss));
	return t;
	}
function print_pkg_start (pkg, start) {
	printf("\033[36;1m%s\033[0m: %s: ", pkg, strftime(tfmt, start));
	}
BEGIN { tfmt="%a %b %d %H:%M:%S %Y"; }
{
	if ($2 == "") {
		printf("Started at %s\n", strftime(tfmt, $1));
		next;
		}
	if ($2 == ":::" || $2 == "***") {
		end=$1;
		print_pkg_start(pkg, start);
		printf("%s", hrtime(end-start));
		if ($2 == "***")
			printf(" \033[31;1mfailed\033[0m");
		printf("\n");
		acctime+=end-start;
		pkg="";
		}
	else {
		if (pkg != "") {
			print_pkg_start(pkg, start);
			printf("\033[31;1minterrupted\033[0m\n");
			pkg="";
			next;
			}
		start=$1;
		pkg=$2;
		}
	}
END {
	if (pkg != "") {
		print_pkg_start(pkg, start);
		printf("\033[31;1minterrupted\033[0m\n");
		}
	printf("Total elapsed time: %s\n", hrtime(acctime));
	}
'
