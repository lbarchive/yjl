#!/bin/sh

cat ../font/stylesheet.css yjlv-base.css | sed "s_url('_url('../font/_g" | yuicompressor.sh --type css -o yjlv.css
