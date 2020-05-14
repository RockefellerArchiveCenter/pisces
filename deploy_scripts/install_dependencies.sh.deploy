#!/bin/bash
set -e

ENV_DIR=env

cd ${ROOT_DIR}

# recreate virtual env
${PYTHON_PATH} -m venv $ENV_DIR --clear

# install dependencies
$ENV_DIR/bin/pip install --upgrade pip
$ENV_DIR/bin/pip install -r requirements.txt
