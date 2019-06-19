#!/bin/bash

# Apply database migrations
if [ ! -f manage.py ]; then
  cd pisces
fi

./wait-for-it.sh db:5432 -- echo "Creating config file"

if [ ! -f pisces/config.py ]; then
    cp pisces/config.py.example pisces/config.py
fi

echo "Apply database migrations"
python manage.py makemigrations && python manage.py migrate

#Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000
