#!/usr/bin/env bash

set -e
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

create_admin_if_needed() {
  if [ -z "$ADMIN_LOGIN" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo "Переменные окружения ADMIN_LOGIN или ADMIN_PASSWORD не найдены. Создаем администратора с логином 'admin' и паролем 'admin'."
    ADMIN_LOGIN="admin"
    ADMIN_PASSWORD="admin"
  fi

  # Создание администратора с логином и паролем
  echo "Создание администратора..."
  eval uv run python src/tools/create_admin.py "$ADMIN_LOGIN" "$ADMIN_PASSWORD" "Admin" "User"
}

apply_migrations

create_admin_if_needed

if [ "$API_PRODUCTION" = "true" ]; then
  # https://fastapi.tiangolo.com/deployment/docker/#replication-number-of-processes
  echo "Запуск приложения в продакшн-режиме..."
  eval uv run fastapi run src/main.py --host 0.0.0.0 --port 8000
else
  echo "Запуск приложения в режиме разработки..."
  eval uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000 --reload
fi
