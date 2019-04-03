#!/bin/bash

# Apply database migrations
echo "Apply database migrations"
./wait-for-it.sh db:5432 -- python manage.py migrate

if [ ! -f pisces/config.py ]; then
    cp pisces/config.py.example pisces/config.py
fi

#Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000
