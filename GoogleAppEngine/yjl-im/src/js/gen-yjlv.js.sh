#!/bin/sh

closure.sh --js=yjlv-base.js --js_output_file=/tmp/yjlv-base.min.js
cat jquery.min.js jquery.jknav.min.js /tmp/yjlv-base.min.js > yjlv.js
