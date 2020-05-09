#!/bin/bash
set -e

ROOT_DIR=/data/app/zodiac/pisces
ENV_DIR=env
PYTHON_PATH=/opt/rh/rh-python36/root/usr/bin/python

cd $ROOT_DIR

# recreate virtual env
$PYTHON_PATH -m venv $ENV_DIR --clear

# install dependencies
$ENV_DIR/bin/pip --upgrade pip
$ENV_DIR/bin/pip install -r requirements.txt
