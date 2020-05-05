#!/bin/bash

echo Running `basename "$0"`

ENV_DIR="env"

# recreate virtual env
python -m venv $ENV_DIR --clear

# install dependencies
env/bin/pip install -r requirements.txt

# set environment variables
set -a
. ./env.txt
set +a

# Run database migrations
env/bin/python manage.py migrate

# Collect static files
env/bin/python manage.py collectstatic --noinput
