#!/bin/bash

urxvtc -name 'dzen-status-cpu' -title 'CPU Status' \
	    -geometry "160x40" +sb \
	    -e htop --sort-key PERCENT_CPU
