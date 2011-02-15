#!/bin/sh

closure.sh --js=yjlv-base.js --js_output_file=/tmp/yjlv-base.min.js
cat jquery.min.js ~/p/lilbtn/src/static/js/itchape.js /tmp/yjlv-base.min.js > yjlv.js
