# Запуск всех контейнеров
run-all:
	docker compose up -d --build

# Запуск асинхронного api
run-api:
	docker compose up -d --build api nginx

# Запуск админки
run-admin:
	docker compose up -d --build web nginx

# Запуск сервиса переноса данных из БД в Elasticsearch
run-etl:
	docker compose up -d --build etl

# Остановка и удаление всех контейнеров
down:
	docker compose down

# Запуск тестов и остановка сервисов
run-functional-tests:
	bash ./theater-async-api/tests/functional/run_tests.sh
