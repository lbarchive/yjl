#!/bin/bash

urxvtc -name 'dzen-status-mem' -title 'CPU Status' \
	    -geometry "160x40" +sb \
	    -e htop --sort-key PERCENT_MEM
