#!/bin/bash

SRC_PATH=../src

mkdir -p pylint
cd pylint

if [[ "$GAE_PATH" == "" ]]; then
	echo "Set environment variable GAE_PATH if Google App Engine can not be found"
	export PYTHONPATH=$SRC_PATH
else
	export PYTHONPATH=$SRC_PATH:$GAE_PATH
fi

pylint --rcfile=../pylintrc $SRC_PATH/*.py $SRC_PATH/brps
