#!/bin/bash

ENV_FILE=".env"
# check if .env file exists, if not create it
if ! grep -q "SECRET_KEY=" "$ENV_FILE"; then
    echo "Generating new SECRET_KEY..."
    # generate a new SECRET_KEY and append it to the .env file
    SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    echo "SECRET_KEY=$SECRET_KEY" >> "$ENV_FILE"
else
    echo "SECRET_KEY already exists in .env, skipping generation."
fi

# Load environment variables from .env file
export $(grep -v '^#' "$ENV_FILE" | xargs)


# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
mkdir -p /var/www/static
chown -R www-data:www-data /var/www/static
python manage.py collectstatic --no-input --clear

# Start Gunicorn server
gunicorn hiddify.wsgi:application --bind 0.0.0.0:8000