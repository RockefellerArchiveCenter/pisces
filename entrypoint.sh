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
python manage.py migrate

# python manage.py shell -c "from django.contrib.auth.models import User; \
#   User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')"

#Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8007
