#!/bin/bash

# Переходим в директорию, где находится скрипт
cd "$(dirname "$0")" || exit

# Запускаем все сервисы в фоновом режиме
docker compose up -d --build

# Ждем завершения entrypoint у сервиса tests
docker compose logs -f tests

# Останавливаем все сервисы
docker compose down
