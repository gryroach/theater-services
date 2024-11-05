#!/usr/bin/env bash

# Сбор статики
./manage.py collectstatic --noinput

# Компиляция переводов
./manage.py compilemessages

# Запуск миграций
./manage.py migrate

# Запуск web-сервера
gunicorn -c gunicorn_config.py config.wsgi:application
