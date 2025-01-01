#!/usr/bin/env bash

# Функция для применения миграций
apply_migrations() {
  echo "Проверка миграций..."
  
  # Проверка, если нужно выполнить миграции
  if [ "$MIGRATE" = "true" ]; then
    echo "Проверяем текущие миграции..."
      if eval uv run alembic current | grep -q "head"; then
        echo "Миграции уже применены или нет новых миграций."
      else
        echo "Миграции не были применены. Применяем миграции..."
        eval uv run alembic upgrade head  # Применение миграций
      fi
  else
    echo "Миграции пропущены."
  fi
}

apply_migrations

if [ "$API_PRODUCTION" = "true" ]; then
  # https://fastapi.tiangolo.com/deployment/docker/#replication-number-of-processes
  echo "Запуск приложения в продакшн-режиме..."
  eval uv run fastapi run src/main.py --host 0.0.0.0 --port 8000
else
  echo "Запуск приложения в режиме разработки..."
  eval uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000 --reload
fi
