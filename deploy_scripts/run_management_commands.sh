#!/bin/bash

ROOT_DIR=/data/app/zodiac/pisces

cd $ROOT_DIR

# Run database migrations
env/bin/python manage.py migrate

# Collect static files
env/bin/python manage.py collectstatic --noinput
