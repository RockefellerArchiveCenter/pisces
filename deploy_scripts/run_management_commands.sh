#!/bin/bash

ROOT_DIR=/data/app/zodiac/pisces

cd $ROOT_DIR

printenv

source /etc/profile.d/pisces.sh

echo "*** Env variables were sourced here."

printenv

# Run database migrations
env/bin/python manage.py migrate

# Collect static files
env/bin/python manage.py collectstatic --noinput
