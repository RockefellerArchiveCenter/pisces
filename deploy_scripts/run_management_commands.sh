#!/bin/bash

ROOT_DIR=/data/app/zodiac/pisces

cd $ROOT_DIR

mv pisces/deploy_config.py pisces/config.py

# Run database migrations
env/bin/python manage.py migrate

# Collect static files
env/bin/python manage.py collectstatic --noinput
