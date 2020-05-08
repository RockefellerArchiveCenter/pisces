#!/bin/bash

ROOT_DIR=/data/app/zodiac/pisces
ENV_DIR=env
PYTHON_PATH=/opt/rh/rh-python36/root/usr/bin/pythons

cd $ROOT_DIR

if [ ! -d $ENV_DIR ]; then
  mkdir $ENV_DIR
fi

# recreate virtual env
$PYTHON_PATH -m venv $ENV_DIR --clear

# install dependencies
$ENV_DIR/bin/pip install -r requirements.txt
