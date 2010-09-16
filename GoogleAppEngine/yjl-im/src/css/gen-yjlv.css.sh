#!/bin/sh

cat ../font/stylesheet.css yjlv-base.css | sed "s_url('_url('../font/_" | yuicompressor.sh --type css -o yjlv.css
